import asyncio

from transmission_rpc import Client, File, Torrent

from config import (
    TRANSMISSION_HOST,
    TRANSMISSION_PASSWORD,
    TRANSMISSION_PORT,
    TRANSMISSION_USERNAME,
)


class TorrentService:
    def __init__(
        self,
        host=TRANSMISSION_HOST,
        port=TRANSMISSION_PORT,
        username=TRANSMISSION_USERNAME,
        password=TRANSMISSION_PASSWORD,
    ):
        self.client = Client(host=host, port=port, username=username, password=password)

    async def get_torrents(self) -> list[Torrent]:
        """Get all torrents from Transmission"""
        return await asyncio.to_thread(self.client.get_torrents)

    async def add_torrent(self, torrent: bytes | str) -> Torrent:
        """Add a torrent to Transmission"""

        return await asyncio.to_thread(
            self.client.add_torrent, torrent=torrent, sequential_download=True
        )

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
