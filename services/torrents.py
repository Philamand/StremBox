import asyncio

from transmission_rpc import Client, File, Torrent

from fastapi import Request
from schemas.users import User


def get_torrent_service(request: Request) -> TorrentService:
    """Get the torrent service for the current user"""
    user: User = request.state.user

    if not user.transmission_host or not user.transmission_port:
        raise ValueError("Transmission host and port are not set")

    return TorrentService(host=user.transmission_host, port=user.transmission_port)


class TorrentService:
    """Service for interacting with Transmission"""

    def __init__(self, host: str, port: int):
        self.client = Client(host=host, port=port)

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
