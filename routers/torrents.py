from fastapi import APIRouter, Depends

from services.torrent_manager import TorrentManager
from utils.security import validate_bearer_token

router = APIRouter(dependencies=[Depends(validate_bearer_token)])


@router.get("/")
async def get_torrent_list(
    torrent_manager: TorrentManager = Depends(),
):
    """Return the list of all torrents."""
    return await torrent_manager.get_torrent_list()


@router.get("/hashes/")
async def get_torrent_hashes(
    torrent_manager: TorrentManager = Depends(),
) -> list[str]:
    """Return a list of all torrent hashes."""
    torrents = await torrent_manager.get_torrent_list()
    return [torrent.hash for torrent in torrents]
