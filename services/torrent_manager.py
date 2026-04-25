import asyncio
import time

import qbittorrentapi
from fastapi import HTTPException
from qbittorrentapi import TorrentFilesList, TorrentInfoList

from config import QBT_HOST, QBT_PASSWORD, QBT_PORT, QBT_USERNAME


class TorrentManager:
    """Manage torrent lifecycle operations via qBittorrent."""

    def __init__(self):
        """Create and configure a qBittorrent client from environment variables."""
        self._client = qbittorrentapi.Client(
            host=QBT_HOST, port=QBT_PORT, username=QBT_USERNAME, password=QBT_PASSWORD
        )

    async def add_torrent_file(self, torrent_file: bytes):
        """Add a torrent file and enable sequential download."""

        def _add_torrent_sync():
            self._client.torrents_add(
                torrent_files=torrent_file, sequential_download=True
            )

        await asyncio.to_thread(_add_torrent_sync)

    async def add_torrent(
        self, hash: str, tracker: str, api_key: str | None, torrent_id: str | None
    ):
        """Add a torrent URL or magnet link and enable sequential download."""

        def _add_torrent_sync():
            if not api_key:
                raise HTTPException(status_code=400, detail="Clé API non configurée")

            if tracker == "c411":
                download_link = f"https://c411.org/api?t=get&id={hash}&apikey={api_key}"
            elif tracker == "torr9":
                download_link = f"https://api.torr9.net/api/v1/torznab/torrents/{torrent_id}/download?passkey={api_key}"
            else:
                raise HTTPException(status_code=400, detail="Tracker non supporté")

            return self._client.torrents_add(
                urls=download_link,
                is_sequential_download=True,
            )

        return await asyncio.to_thread(_add_torrent_sync)

    async def check_torrent(self, hash: str) -> bool:
        """Check if a torrent is still active."""

        def _check_torrent_sync():
            torrents = self._client.torrents_info(torrent_hashes=hash)
            return torrents != []

        return await asyncio.to_thread(_check_torrent_sync)

    async def wait_until_added(
        self, hash: str, timeout: float = 30.0, poll_interval: float = 0.5
    ):
        """Poll qBittorrent until a torrent appears or raise on timeout."""

        def _wait_until_added_sync():
            deadline = time.monotonic() + timeout
            while time.monotonic() < deadline:
                torrents = self._client.torrents_info(torrent_hashes=hash)
                if torrents:
                    return
                time.sleep(poll_interval)

            raise HTTPException(
                status_code=504,
                detail=f"Timed out after {int(timeout)}s waiting for torrent to be added.",
            )

        return await asyncio.to_thread(_wait_until_added_sync)

    async def get_torrent_files(self, hash: str) -> TorrentFilesList:
        """Return file entries for a given torrent hash."""

        def _get_torrent_files_sync():
            return self._client.torrents_files(hash=hash)

        return await asyncio.to_thread(_get_torrent_files_sync)

    async def get_torrent_list(self) -> TorrentInfoList:
        """Return the list of all torrents."""

        def _get_torrent_list_sync():
            return self._client.torrents_info()

        return await asyncio.to_thread(_get_torrent_list_sync)

    async def ensure_torrent_available(
        self,
        hash: str,
        tracker: str | None,
        api_key: str | None,
        torrent_id: str | None,
    ):
        """Ensure the torrent is available, downloading if necessary."""
        torrent_exists = await self.check_torrent(hash)

        if torrent_exists:
            return

        if not tracker:
            raise HTTPException(status_code=404, detail="Torrent introuvable")

        await self.add_torrent(hash, tracker, api_key, torrent_id)
        await self.wait_until_added(hash)
