from typing import Annotated

from fastapi import APIRouter, Depends, File

from services.torrent_manager import TorrentManager
from utils.security import validate_bearer_token

router = APIRouter(dependencies=[Depends(validate_bearer_token)])


@router.get("/")
async def get_torrent_list(
    torrent_manager: TorrentManager = Depends(),
):
    """Return the list of all torrents."""
    return await torrent_manager.get_torrent_list()


@router.post("/")
async def add_torrent_file(
    torrent_file: Annotated[bytes, File()],
    torrent_manager: TorrentManager = Depends(),
):
    """Add a torrent file."""
    await torrent_manager.add_torrent_file(torrent_file)
    return {"message": "Fichier torrent ajouté avec succès"}


@router.delete("/{hash}")
async def delete_torrent(
    hash: str,
    torrent_manager: TorrentManager = Depends(),
):
    """Delete a torrent by hash."""
    await torrent_manager.delete_torrent(hash)
    return {"message": "Torrent supprimé avec succès"}


@router.get("/hashes/")
async def get_torrent_hashes(
    torrent_manager: TorrentManager = Depends(),
) -> list[str]:
    """Return a list of all torrent hashes."""
    torrents = await torrent_manager.get_torrent_list()
    return [torrent.hash for torrent in torrents]
