import os

from http_client import get_session


class TraktError(Exception):
    pass


class TraktService:
    def __init__(self):
        self.base_url = "https://api.trakt.tv"
        self.api_key = os.environ.get("TRAKT_API_KEY", None)
        self.access_token = os.environ.get("TRAKT_ACCESS_TOKEN", None)

    def _get_headers(self) -> dict:
        if not self.api_key or not self.access_token:
            raise TraktError("Missing Trakt API key or access token")
        return {
            "accept": "application/json",
            "User-Agent": "readme/1.0",
            "trakt-api-version": "2",
            "trakt-api-key": self.api_key,
            "authorization": f"Bearer {self.access_token}",
        }

    async def get_unwatched_movies(self) -> list[int]:
        url = f"{self.base_url}/users/me/watchlist/movies/title"
        params = {"hide": "unreleased"}

        session = get_session()
        async with session.get(
            url, params=params, headers=self._get_headers()
        ) as response:
            data = await response.json()
            return [item["movie"]["ids"]["tmdb"] for item in data]

    async def get_unwatched_shows(self) -> list[int]:
        url = f"{self.base_url}/users/me/watchlist/shows/title"
        params = {"hide": "unreleased"}

        session = get_session()
        async with session.get(
            url, params=params, headers=self._get_headers()
        ) as response:
            data = await response.json()
            return [item["show"]["ids"]["tmdb"] for item in data]

    async def get_unfinished_shows(self) -> list[int]:
        url = f"{self.base_url}/users/me/watched/shows"
        params = {"hidden": "false", "specials": "false"}

        session = get_session()
        async with session.get(
            url, params=params, headers=self._get_headers()
        ) as response:
            data = await response.json()
            return [
                item["show"]["ids"]["tmdb"]
                for item in data
                if item["plays"] < item["show"]["aired_episodes"]
            ]
