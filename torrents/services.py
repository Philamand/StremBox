import asyncio

from fastapi import Request
from transmission_rpc import Client, File, Torrent

from core.config import TRANSMISSION_URL
from torrents.utils import get_torrent_size
from users.schemas import UserData


class TorrentService:
    """Service for interacting with Transmission"""

    def __init__(self, request: Request):
        user: UserData = request.state.user

        if not user.transmission_data or not user.transmission_data.port:
            raise ValueError("Transmission port is not set")

        self.client = Client(host=TRANSMISSION_URL, port=user.transmission_data.port)

    async def get_torrents(self) -> list[Torrent]:
        """Get all torrents from Transmission"""
        return await asyncio.to_thread(self.client.get_torrents)

    async def add_torrent(
        self,
        torrent: bytes | str,
        max_size: int,
    ) -> None:
        """Add a torrent to Transmission after verifying its size.

        The total content size is compared against *max_size* (bytes).  If the
        torrent is larger, a ``ValueError`` is raised and the torrent is never
        left running in Transmission.

        * **bytes** input (.torrent file content): the size is extracted from
          the file metadata *before* the torrent is added to Transmission.
        * **str** input (magnet link or URL): the torrent is added in a paused
          state first.  Once Transmission has fetched the metadata and the
          total size becomes known, the size check is performed.  If the torrent
          is too large it is immediately removed; otherwise it is started.

        Raises:
            ValueError: if the torrent size exceeds *max_size*, or if metadata
                could not be retrieved within the timeout window.
        """
        if isinstance(torrent, bytes):
            size = get_torrent_size(torrent)
            if size > max_size:
                raise ValueError(
                    "Pas assez d'espace disponible pour télécharger ce torrent."
                )
            await asyncio.to_thread(
                self.client.add_torrent, torrent=torrent, sequential_download=True
            )
            return

        added: Torrent = await asyncio.to_thread(
            self.client.add_torrent,
            torrent=torrent,
            paused=True,
            sequential_download=True,
        )

        async def _poll_size(hash_str: str, interval: float = 1.0) -> int:
            """Poll Transmission until the torrent metadata (total size) is available."""
            while True:
                t: Torrent = await asyncio.to_thread(self.client.get_torrent, hash_str)
                if t.total_size > 0:
                    return t.total_size
                await asyncio.sleep(interval)

        try:
            size = await asyncio.wait_for(_poll_size(added.hashString), timeout=60.0)
        except asyncio.TimeoutError:
            await asyncio.to_thread(
                self.client.remove_torrent, added.hashString, delete_data=True
            )
            raise ValueError(
                "Temps expiré : les métadonnées du torrent n'ont pas été récupérées dans le temps imparti."
            )

        if size > max_size:
            await asyncio.to_thread(
                self.client.remove_torrent, added.hashString, delete_data=True
            )
            raise ValueError(
                "Pas assez d'espace disponible pour télécharger le torrent."
            )

        await asyncio.to_thread(self.client.start_torrent, added.hashString)

    async def remove_torrent(
        self, torrent_hash: str, delete_files: bool = False
    ) -> None:
        """Remove a torrent from Transmission"""
        await asyncio.to_thread(
            self.client.remove_torrent, torrent_hash, delete_data=delete_files
        )

    async def get_torrent_files(self, torrent_hash: str) -> list[File]:
        """Get the files of a torrent"""
        torrent = await asyncio.to_thread(self.client.get_torrent, torrent_hash)
        return await asyncio.to_thread(torrent.get_files)
