import aiohttp


class LibreBoxService:
    """Service for interacting with LibreBox-related endpoints."""

    def __init__(self, base_url: str, bearer_token: str):
        self.base_url = base_url
        self.bearer_token = bearer_token

    async def get_torrent_hashes(self) -> list[str]:
        """Get a list of torrent hashes from the API."""
        async with aiohttp.ClientSession() as session:
            headers = {"Authorization": f"Bearer {self.bearer_token}"}
            async with session.get(
                f"{self.base_url}/torrents/hashes/", headers=headers
            ) as response:
                return await response.json()
