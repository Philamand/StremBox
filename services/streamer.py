import aiohttp


class StreamerService:
    """Service for interacting with streamer-related endpoints."""

    def __init__(self, session: aiohttp.ClientSession, base_url: str):
        self.session = session
        self.base_url = base_url

    async def get_torrent_hashes(self) -> list[str]:
        """Get a list of torrent hashes from the API."""
        async with self.session.get(f"{self.base_url}/torrents/hashes/") as response:
            return await response.json()
