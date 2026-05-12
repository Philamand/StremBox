from typing import Annotated

from fastapi import APIRouter, Depends

from services.torrents import TorrentService
from utils.security import validate_bearer_token

api_router = APIRouter(prefix="/api", dependencies=[Depends(validate_bearer_token)])


@api_router.get("/hashes/")
async def get_hashes(
    torrent_service: Annotated[TorrentService, Depends()],
):
    """Get all torrent hashes from Transmission."""
    torrents = await torrent_service.get_torrents()
    hashes_dict = {}
    for torrent in torrents:
        hashes_dict[torrent.hashString] = [file.name for file in torrent.get_files()]
    return hashes_dict
