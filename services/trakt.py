import os


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
