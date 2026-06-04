import asyncio
import logging
import urllib.parse
import xml.etree.ElementTree as ET
from typing import Any, Dict, List, Optional

import aiohttp
from aiohttp import ClientTimeout

from schemas.stremio import (
    StremioStreamData,
    StremioStreamsResponse,
)
from schemas.users import UserData
from services.bauxite import BauxiteService
from utils.stremio import (
    check_season_episode,
    check_title_match,
    extract_download_params,
    get_torrent_name,
    get_torrent_tracker_and_id,
    parse_torrent_name,
    sort_dicts_by_seeders_desc,
)


class C411Service:
    """
    Client for the C411 torznab-style API.

    This class encapsulates contacting the C411 API and converting returned
    results into normalized Python dictionaries suitable for downstream code.

    Args:
        apikey: API key string to attach to requests. If falsy, searches will
                short-circuit and return an empty list.

    Example:
        svc = C411Service(apikey="...")    # constructed by dependency provider
        results = await svc.search_movie(title="Inception", year=2010)
    """

    apikey: str
    base_url: str

    def __init__(self, apikey: str) -> None:
        """
        Initialize the C411Service with an API key.

        Args:
            apikey (str): The API key required for C411 API authentication.
        """
        self.apikey = apikey
        self.base_url = "https://c411.org/api"

    async def search(self, params: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Perform a generic search against the C411 API and normalize the response.

        The method expects `params` to contain query parameters appropriate for
        the c411 API. The API key and JSON output format are automatically added.

        Behavior and error handling:
        - If the client was created without an API key, returns an empty list.
        - On non-200 responses or exceptions, logs details and returns an empty list.
        - Normalizes the XML->JSON response variations (single item -> list,
          torznab attributes as dict vs list).

        Args:
            params: Query parameters for the C411 API call.

        Returns:
            A list of normalized result dictionaries. Each dictionary contains
            keys such as "name", "size", "tracker_name", "info_hash", "magnet",
            "link", "source", "seeders", "leechers".
        """
        if not self.apikey:
            return []

        params["apikey"] = self.apikey
        params["o"] = "json"

        # Log request (masking apikey)
        log_params = params.copy()
        log_params["apikey"] = "***APIKEY***"
        logging.info(
            f"C411 Search: {self.base_url}?{urllib.parse.urlencode(log_params)}"
        )

        async with aiohttp.ClientSession(trust_env=True) as session:
            try:
                async with session.get(
                    self.base_url, params=params, timeout=ClientTimeout(total=20)
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        channel = data.get("channel", {})
                        items = channel.get("item", [])

                        # Handle single item case (JSON conversion of XML sometimes makes single item an object instead of list)
                        if isinstance(items, dict):
                            items = [items]

                        logging.info(f"C411 found {len(items)} results")

                        normalized = []
                        for res in items:
                            # Extract torznab attributes
                            attrs = res.get("torznab:attr", [])
                            if isinstance(attrs, dict):
                                attrs = [attrs]

                            info_hash = None
                            seeders = 0
                            leechers = 0

                            for attr in attrs:
                                attr_data = attr.get("@attributes", {})
                                name = attr_data.get("name")
                                value = attr_data.get("value")

                                if name == "infohash":
                                    info_hash = value
                                elif name == "seeders":
                                    seeders = int(value) if value else 0
                                    if leechers != 0:
                                        leechers -= seeders
                                elif name == "peers":
                                    if seeders != 0 and value:
                                        leechers = int(value) - seeders
                                    else:
                                        leechers = int(value) if value else 0

                            # Fallback hash to guid if infohash not found (guid is often hash in torznab)
                            if not info_hash:
                                info_hash = res.get("guid")

                            enclosure = res.get("enclosure", {}).get("@attributes", {})
                            download_link = enclosure.get("url")

                            item = {
                                "name": res.get("title"),
                                "size": int(res.get("size", 0)),
                                "tracker_name": "C411",
                                "info_hash": info_hash,
                                "magnet": None,
                                "link": download_link,
                                "source": "c411",
                                "seeders": seeders,
                                "leechers": leechers,
                            }
                            normalized.append(item)
                        return normalized
                    else:
                        logging.warning(f"C411 Error {response.status}")
                        text = await response.text()
                        logging.warning(f"C411 Body: {text[:200]}")
            except Exception as e:
                logging.error(f"C411 Exception: {e}")
        return []

    async def search_movie(
        self,
        title: Optional[str] = None,
        year: Optional[int] = None,
        imdb_id: Optional[str] = None,
        tmdb_id: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        Search for movies using title/year or external identifiers.

        The method prefers external identifiers when provided (IMDb or TMDB).
        If an IMDb id is supplied without the leading "tt" it will be prepended.

        Args:
            title: Optional movie title (used when no external id is provided).
            year: Optional release year.
            imdb_id: Optional IMDb id (with or without "tt" prefix).
            tmdb_id: Optional TMDB id.

        Returns:
            A list of normalized result dictionaries as returned by `search`.
        """
        params = {"t": "movie"}
        if imdb_id:
            if not str(imdb_id).startswith("tt"):
                imdb_id = f"tt{imdb_id}"
            params["imdbid"] = imdb_id
        elif tmdb_id:
            params["tmdbid"] = tmdb_id
        else:
            params["q"] = f"{title} {year}"

        return await self.search(params)

    async def search_series(
        self,
        title: Optional[str] = None,
        season: Optional[int] = None,
        episode: Optional[int] = None,
        imdb_id: Optional[str] = None,
        tmdb_id: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        Search for TV series torrents (optionally constrained by season/episode).

        If `imdb_id` or `tmdb_id` is provided it will use those identifiers;
        otherwise it will use a text query (title) and optionally include season
        and episode filters where supported by the tracker.

        Args:
            title: Optional series title (used when no external id provided).
            season: Optional season number.
            episode: Optional episode number.
            imdb_id: Optional IMDb id (prepended with "tt" if necessary).
            tmdb_id: Optional TMDB id.

        Returns:
            A list of normalized result dictionaries as returned by `search`.
        """
        params = {"t": "tvsearch"}
        if imdb_id:
            if not str(imdb_id).startswith("tt"):
                imdb_id = f"tt{imdb_id}"
            params["imdbid"] = imdb_id
        elif tmdb_id:
            params["tmdbid"] = tmdb_id
        elif title:
            params["q"] = title

        # Torznab filters for season/episode if supported by tracker
        if season is not None:
            params["season"] = str(season)
        if episode is not None:
            params["episode"] = str(episode)

        return await self.search(params)


class Torr9Service:
    def __init__(self, passkey):
        self.passkey = passkey
        self.base_url = "https://api.torr9.net/api/v1/torznab"

    async def search(self, params):
        if not self.passkey:
            return []

        params["apikey"] = self.passkey

        # Log request (masking passkey)
        log_params = params.copy()
        log_params["apikey"] = "***PASSKEY***"
        logging.info(
            f"Torr9 Search: {self.base_url}?{urllib.parse.urlencode(log_params)}"
        )

        async with aiohttp.ClientSession(trust_env=True) as session:
            try:
                async with session.get(
                    self.base_url, params=params, timeout=ClientTimeout(total=20)
                ) as response:
                    if response.status == 200:
                        text = await response.text()
                        return self._parse_xml(text)
                    else:
                        logging.warning(f"Torr9 Error {response.status}")
                        body = await response.text()
                        logging.warning(f"Torr9 Body: {body[:200]}")
            except Exception as e:
                logging.error(f"Torr9 Exception: {e}")
        return []

    def _parse_xml(self, xml_text):
        """Parse Torznab XML response"""
        try:
            root = ET.fromstring(xml_text)
        except ET.ParseError as e:
            logging.error(f"Torr9 XML Parse Error: {e}")
            return []

        # Torznab namespace
        ns = {"torznab": "http://torznab.com/schemas/2015/feed"}

        items = root.findall(".//item")
        logging.info(f"Torr9 found {len(items)} results")

        normalized = []
        for item in items:
            title = item.findtext("title", "")
            guid = item.findtext("guid", "")
            size_text = item.findtext("size", "0")

            # Enclosure (download link)
            enclosure = item.find("enclosure")
            download_link = enclosure.get("url", "") if enclosure is not None else ""

            # Torznab attributes
            info_hash = None
            seeders = 0
            leechers = 0

            for attr in item.findall("torznab:attr", ns):
                name = attr.get("name")
                value = attr.get("value")
                if name == "infohash":
                    info_hash = value.lower() if value else None
                elif name == "seeders":
                    seeders = int(value) if value else 0
                    if leechers != 0:
                        leechers -= seeders
                elif name == "peers":
                    if seeders != 0 and value:
                        leechers = int(value) - seeders
                    else:
                        leechers = int(value) if value else 0

            # Fallback to guid as hash
            if not info_hash:
                info_hash = guid.lower() if guid else None

            result = {
                "name": title,
                "size": int(size_text) if size_text else 0,
                "tracker_name": "Torr9",
                "info_hash": info_hash,
                "magnet": None,
                "link": download_link,
                "source": "torr9",
                "seeders": seeders,
                "leechers": leechers,
            }
            normalized.append(result)

        return normalized

    async def search_movie(self, title=None, year=None, imdb_id=None, tmdb_id=None):
        params = {"t": "movie"}
        if imdb_id:
            if not str(imdb_id).startswith("tt"):
                imdb_id = f"tt{imdb_id}"
            params["imdbid"] = imdb_id
        elif tmdb_id:
            params["tmdbid"] = tmdb_id
        else:
            params["q"] = f"{title} {year}"

        return await self.search(params)

    async def search_series(
        self, title=None, season=None, episode=None, imdb_id=None, tmdb_id=None
    ):
        params = {"t": "tvsearch"}
        if imdb_id:
            if not str(imdb_id).startswith("tt"):
                imdb_id = f"tt{imdb_id}"
            params["imdbid"] = imdb_id
        elif tmdb_id:
            params["tmdbid"] = tmdb_id
        elif title:
            params["q"] = title

        # Torznab filters for season/episode
        if season is not None:
            params["season"] = season
        if episode is not None:
            params["episode"] = episode

        return await self.search(params)


class StremioOrchestrationService:
    """
    Orchestrates tracker searches, DB torrent upserts, and stream-link creation.

    This service is the single entry point for the Stremio stream endpoint.
    It delegates to the underlying tracker clients and DB-backed services, keeping
    all business logic out of the router.

    Args:
        c411_service: Configured C411 tracker client.
        torr9_service: Configured Torr9 tracker client.
        torrent_service: DB-backed torrent service (get/create records).
        stream_service: Redis-backed stream link service.
    """

    def __init__(
        self,
        librebox_url: str,
        librebox_token: str,
        c411_service: C411Service | None = None,
        torr9_service: Torr9Service | None = None,
    ) -> None:
        self.c411 = c411_service
        self.torr9 = torr9_service
        self.librebox_url = librebox_url
        self.librebox_token = librebox_token

    async def _search_movie(self, imdb_id: str) -> list[dict]:
        """Run parallel C411 + Torr9 searches for a movie and return deduplicated results."""
        name, year = await get_torrent_name(imdb_id, "movie")
        if self.c411 and self.torr9:
            c411_results, torr9_results = await asyncio.gather(
                self.c411.search_movie(imdb_id=imdb_id),
                self.torr9.search_movie(imdb_id=imdb_id),
            )
        elif self.c411:
            c411_results = await self.c411.search_movie(imdb_id=imdb_id)
            torr9_results = []
        elif self.torr9:
            torr9_results = await self.torr9.search_movie(imdb_id=imdb_id)
            c411_results = []
        else:
            return []
        results: list[dict] = c411_results
        for r in torr9_results:
            if check_title_match(r["name"], None, name, year, True):
                results.append(r)
        return results

    async def _search_series(
        self, imdb_id: str, season: int, episode: int
    ) -> list[dict]:
        """Run parallel C411 + Torr9 searches for a series episode and return deduplicated results."""
        name, year = await get_torrent_name(imdb_id, "series")
        if self.c411 and self.torr9:
            c411_results, torr9_results = await asyncio.gather(
                self.c411.search_series(
                    season=season, episode=episode, imdb_id=imdb_id
                ),
                self.torr9.search_series(
                    season=season, episode=episode, imdb_id=imdb_id
                ),
            )
        elif self.c411:
            c411_results = await self.c411.search_series(
                season=season, episode=episode, imdb_id=imdb_id
            )
            torr9_results = []
        elif self.torr9:
            torr9_results = await self.torr9.search_series(
                season=season, episode=episode, imdb_id=imdb_id
            )
            c411_results = []
        else:
            return []
        results: list[dict] = c411_results
        for r in torr9_results:
            if check_season_episode(r["name"], season, episode) and check_title_match(
                r["name"], None, name, year, False
            ):
                results.append(r)
        return results

    async def get_streams(
        self, type: str, id: str, user: UserData
    ) -> StremioStreamsResponse:
        """Build a ``StremioStreamsResponse`` for *type*/*id* on behalf of *user*.

        Args:
            type: ``"movie"`` or ``"series"``.
            id: IMDb id for movies; ``"{imdbid}:{season}:{episode}"`` for series.
            user: Authenticated user (embedded in created stream links).

        Returns:
            A ``StremioStreamsResponse`` with fast (⚡️) streams first.
        """
        bauxite_service = BauxiteService(self.librebox_url, self.librebox_token)
        hashes = await bauxite_service.get_torrent_hashes()

        if type == "series":
            parts = id.split(":")
            imdb_id = parts[0]
            season = int(parts[1])
            episode = int(parts[2])
            results = await self._search_series(imdb_id, season, episode)
        else:
            results = await self._search_movie(id)
            season = None
            episode = None

        if not results:
            return StremioStreamsResponse(streams=[])

        results = sort_dicts_by_seeders_desc(results)

        fast_streams: list[StremioStreamData] = []
        slow_streams: list[StremioStreamData] = []

        for result in results:
            tracker, torrent_id = get_torrent_tracker_and_id(result["link"])

            if tracker == "c411":
                api_key = user.c411_key
            elif tracker == "torr9":
                api_key = user.torr9_key
            else:
                api_key = None

            details = parse_torrent_name(result["name"])

            if result["info_hash"] in hashes.keys():
                torrent = hashes[result["info_hash"]]

                if torrent["percent_done"] < 1:
                    speed_emoji = "🐢 "
                else:
                    speed_emoji = "⚡️ "

                if len(torrent) == 1:
                    file_path = torrent["files"][0]
                else:
                    for filename in torrent["files"]:
                        if check_season_episode(filename, season, episode):
                            file_path = filename
                            break
                    if not file_path:
                        file_path = torrent["files"][0]
                stream_url = f"{self.librebox_url}/static/{file_path}"
            else:
                speed_emoji = ""
                stream_url = f"{self.librebox_url}/streams/download/{self.librebox_token}/{result['info_hash']}?tracker={tracker}&api_key={api_key}"
                if tracker == "torr9":
                    stream_url += f"&torrent_id={torrent_id}"
                if season and episode:
                    stream_url += f"&season={season}&episode={episode}"

            stream = StremioStreamData(
                title=(
                    f"{speed_emoji}{result['name']}\n"
                    f"{details}\n"
                    f"📤 {result['seeders']}  📥 {result['leechers']} | {result['tracker_name']}\n"
                    f"💾 {result['size'] / 1024 / 1024 / 1024:.2f} GB"
                ),
                url=stream_url,
                filename=file_path,
                videoSize=int(result["size"]),
            )
            if speed_emoji == "⚡️ " or speed_emoji == "🐢 ":
                fast_streams.append(stream)
            else:
                slow_streams.append(stream)

        if len(fast_streams) == 0 and len(slow_streams) > 0:
            fast_stream = slow_streams[0]
            download_request = extract_download_params(fast_stream.url)
            await bauxite_service.download_torrent(download_request)
            fast_stream.title = f"🐢 {fast_stream.title}"
            fast_stream.url = f"{self.librebox_url}/static/{fast_stream.filename}"
            fast_streams.append(fast_stream)
            slow_streams = slow_streams[1:]

        response = StremioStreamsResponse(streams=fast_streams + slow_streams)

        return response
