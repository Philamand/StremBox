import time

import qbittorrentapi
from fastapi import HTTPException
from qbittorrentapi import TorrentFilesList

from config import C411_API_KEY, QBT_HOST, QBT_PASSWORD, QBT_PORT, QBT_USERNAME


class TorrentManager:
    """Manage torrent lifecycle operations via qBittorrent."""

    def __init__(self):
        """Create and configure a qBittorrent client from environment variables."""
        self._client = qbittorrentapi.Client(
            host=QBT_HOST, port=QBT_PORT, username=QBT_USERNAME, password=QBT_PASSWORD
        )
        self.c411_api_key = C411_API_KEY

    def add_torrent(self, hash: str, tracker: str):
        """Add a torrent URL or magnet link and enable sequential download."""
        if tracker == "c411":
            if not self.c411_api_key:
                raise HTTPException(
                    status_code=400, detail="Clé API C411 non configurée"
                )
            download_link = (
                f"https://c411.org/api?t=get&id={hash}&apikey={self.c411_api_key}"
            )
        else:
            raise HTTPException(status_code=400, detail="Tracker non supporté")

        return self._client.torrents_add(
            urls=download_link,
            is_sequential_download=True,
        )

    def check_torrent(self, hash: str) -> bool:
        """Check if a torrent is still active."""
        torrents = self._client.torrents_info(torrent_hashes=hash)
        return torrents != []

    def wait_until_added(
        self, hash: str, timeout: float = 30.0, poll_interval: float = 0.5
    ):
        """Poll qBittorrent until a torrent appears or raise on timeout."""
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

    def get_files(self, hash: str) -> TorrentFilesList:
        """Return file entries for a given torrent hash."""
        return self._client.torrents_files(hash=hash)
