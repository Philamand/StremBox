import os

from http_client import get_session
from schemas.trakt import TraktHistoryEntry, TraktSeason


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

    async def get_unwatched_movies(self, user_slug: str) -> list[int]:
        url = f"{self.base_url}/users/{user_slug}/watchlist/movies/title"
        params = {"hide": "unreleased"}

        session = get_session()
        async with session.get(
            url, params=params, headers=self._get_headers()
        ) as response:
            data = await response.json()
            return [item["movie"]["ids"]["tmdb"] for item in data]

    async def get_unwatched_shows(self, user_slug: str) -> list[int]:
        url = f"{self.base_url}/users/{user_slug}/watchlist/shows/title"
        params = {"hide": "unreleased"}

        session = get_session()
        async with session.get(
            url, params=params, headers=self._get_headers()
        ) as response:
            data = await response.json()
            return [item["show"]["ids"]["tmdb"] for item in data]

    async def get_unfinished_shows(self, user_slug: str) -> list[int]:
        url = f"{self.base_url}/users/{user_slug}/watched/shows"
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

    async def get_all_seasons(self, show_id: str) -> list[TraktSeason]:
        url = f"{self.base_url}/shows/{show_id}/seasons"
        params = {"extended": "episodes"}

        session = get_session()
        async with session.get(
            url, params=params, headers=self._get_headers()
        ) as response:
            data = await response.json()
            return [TraktSeason.model_validate(season) for season in data]

    async def get_show_history(
        self, user_slug: str, item_id: str
    ) -> list[TraktHistoryEntry]:
        url = f"{self.base_url}/users/{user_slug}/history/shows/{item_id}"

        session = get_session()
        async with session.get(url, headers=self._get_headers()) as response:
            data = await response.json()
            return [TraktHistoryEntry.model_validate(entry) for entry in data]
