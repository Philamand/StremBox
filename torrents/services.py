import asyncio
from typing import Annotated

from fastapi import Depends, Request
from transmission_rpc import Client, File, Torrent

from core.config import settings
from torrents.utils import get_torrent_size
from users.schemas import UserData


class TorrentService:
    """Service for interacting with Transmission"""

    def __init__(self, request: Request):
        user: UserData = request.state.user

        if not user.transmission_data or not user.transmission_data.port:
            raise ValueError("Transmission port is not set")

        self.client = Client(
            host=settings.transmission_url, port=user.transmission_data.port
        )

    async def get_torrents(self) -> list[Torrent]:
        """Get all torrents from Transmission"""
        return await asyncio.to_thread(self.client.get_torrents)

    async def get_torrent(self, hash_string: str) -> Torrent:
        """Get a single torrent by its info-hash."""
        return await asyncio.to_thread(self.client.get_torrent, hash_string)

    async def add_torrent(
        self,
        torrent: bytes | str,
        max_size: int,
        start: bool = True,
    ) -> str:
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

        Before starting, the method checks whether the download content already
        exists on disk.  If it does, ``verify_torrent`` is called to check the
        integrity of the existing data before the torrent is started.

        Returns:
            The info-hash string of the added torrent.

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
            added = await asyncio.to_thread(
                self.client.add_torrent,
                torrent=torrent,
                sequential_download=True,
                paused=True,
            )
        else:
            added = await asyncio.to_thread(
                self.client.add_torrent,
                torrent=torrent,
                sequential_download=True,
            )

            async def _poll_size(hash_str: str, interval: float = 1.0) -> int:
                while True:
                    t: Torrent = await asyncio.to_thread(
                        self.client.get_torrent, hash_str
                    )
                    if t.total_size > 0:
                        return t.total_size
                    await asyncio.sleep(interval)

            try:
                size = await asyncio.wait_for(
                    _poll_size(added.hashString), timeout=60.0
                )
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

        if start:
            await asyncio.to_thread(self.client.start_torrent, added.hashString)

        await asyncio.to_thread(self.client.verify_torrent, added.hashString)

        return added.hashString

    async def start_torrent(self, hash_string: str) -> None:
        """Start the torrent with the given hash string."""
        await asyncio.to_thread(self.client.start_torrent, hash_string)

    async def stop_torrent(self, hash_string: str) -> None:
        """Stop the torrent with the given hash string."""
        await asyncio.to_thread(self.client.stop_torrent, hash_string)

    async def wait_for_download_start(
        self, hash_string: str, timeout: float = 15.0, min_percent: float = 0.0
    ) -> None:
        """Wait until the torrent actually starts downloading data.

        Polls Transmission every 500 ms until *rate_download* goes above
        zero **and** at least *min_percent* (0.0 – 1.0) of the torrent has
        been downloaded.

        If the timeout is reached but data is already flowing
        (*rate_download > 0*) the method returns anyway so the caller can
        proceed with whatever data is available.  A ``ValueError`` is only
        raised when absolutely no data has been transferred within *timeout*
        seconds.
        """

        async def _poll(needs_percent: float) -> bool:
            while True:
                t: Torrent = await asyncio.to_thread(
                    self.client.get_torrent, hash_string
                )
                if t.rate_download > 0 and t.percent_done >= needs_percent:
                    return True
                await asyncio.sleep(0.5)

        try:
            await asyncio.wait_for(_poll(min_percent), timeout=timeout)
        except asyncio.TimeoutError:
            t = await asyncio.to_thread(self.client.get_torrent, hash_string)
            if t.rate_download > 0:
                return
            raise ValueError("Le téléchargement n'a pas démarré dans le temps imparti.")

    async def wait_for_download_complete(
        self,
        hash_string: str,
        timeout: float | None = None,
        file_name: str | None = None,
    ) -> None:
        """Wait until a torrent (or a specific file) finishes downloading.

        Polls Transmission every second.  If *file_name* is ``None`` (the
        default) the method waits for the entire torrent to reach 100 %.
        When a file name is given only that file's completion is checked.

        If *timeout* is ``None`` the method waits indefinitely; otherwise a
        ``ValueError`` is raised when the deadline is exceeded.

        Raises:
            ValueError: if *file_name* does not match any file in the torrent,
                or if the timeout is reached before the download completes.
        """

        async def _poll_torrent() -> bool:
            while True:
                t: Torrent = await asyncio.to_thread(
                    self.client.get_torrent, hash_string
                )
                if t.percent_done >= 1.0:
                    return True
                await asyncio.sleep(1.0)

        async def _poll_file(name: str) -> bool:
            torrent: Torrent = await asyncio.to_thread(
                self.client.get_torrent, hash_string
            )
            file_list: list[File] = await asyncio.to_thread(torrent.get_files)

            target_id: int | None = None
            for f in file_list:
                if f.name == name:
                    target_id = f.id
                    break
            if target_id is None:
                raise ValueError(f"Aucun fichier nommé '{name}' dans le torrent.")

            while True:
                torrent = await asyncio.to_thread(self.client.get_torrent, hash_string)
                file_list = await asyncio.to_thread(torrent.get_files)
                for f in file_list:
                    if f.id == target_id:
                        if f.completed >= f.size:
                            return True
                        break
                await asyncio.sleep(1.0)

        coro = _poll_torrent() if file_name is None else _poll_file(file_name)

        try:
            await asyncio.wait_for(coro, timeout=timeout)
        except asyncio.TimeoutError:
            raise ValueError(
                "Le téléchargement n'est pas terminé dans le temps imparti."
            )

    async def remove_torrent(
        self, torrent_hash: str, delete_files: bool = False
    ) -> None:
        """Remove a torrent from Transmission"""
        await asyncio.to_thread(
            self.client.remove_torrent, torrent_hash, delete_data=delete_files
        )

    async def verify_torrents_by_file(self, file_path: str) -> None:
        """Verify all torrents that contain a specific file.

        Searches through all torrents to find those containing a file with
        the exact matching path.  For each matching torrent, calls
        ``client.verify_torrent()`` to check the integrity of the data.

        Args:
            file_path: The file path to search for in torrents.
        """
        torrents = await self.get_torrents()
        matching_hashes = []

        for torrent in torrents:
            files = await self.get_torrent_files(torrent.hashString)
            for file in files:
                if file.name == file_path:
                    matching_hashes.append(torrent.hashString)
                    break

        for hash_str in matching_hashes:
            await asyncio.to_thread(self.client.verify_torrent, hash_str)

    async def get_torrent_files(self, torrent_hash: str) -> list[File]:
        """Get the files of a torrent"""
        torrent = await asyncio.to_thread(self.client.get_torrent, torrent_hash)
        return await asyncio.to_thread(torrent.get_files)


def get_torrent_service(request: Request) -> TorrentService:
    """Factory dependency that creates a TorrentService from the current request."""
    return TorrentService(request)


TorrentServiceDep = Annotated[TorrentService, Depends(get_torrent_service)]
