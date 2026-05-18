from typing import Annotated, Optional

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import FileResponse, RedirectResponse

from files.services import FileManager
from streams.utils import resolve_file_path
from torrents.services import TorrentService
from users.security import check_user_key

router = APIRouter(prefix="/streams", dependencies=[Depends(check_user_key)])


@router.get("/{user_key}")
async def get_stream(
    request: Request,
    file_manager: Annotated[FileManager, Depends()],
    torrent_service: Annotated[TorrentService, Depends()],
    file_path: Optional[str] = None,
    torrent_hash: Optional[str] = None,
    season: Optional[int] = None,
    episode: Optional[int] = None,
) -> FileResponse:
    """Return a stream of the file at the given path."""
    if not file_path and not torrent_hash:
        raise HTTPException(
            status_code=400, detail="Either file_path or torrent_hash is required"
        )

    if torrent_hash:
        torrent_files = await torrent_service.get_torrent_files(torrent_hash)
        file_path = resolve_file_path(
            torrent_files[0].name,
            request.state.user.transmission_data.download_folder,
            season,
            episode,
        )

    path = file_manager.get_path(file_path)

    if not await file_manager.exists(path):
        raise HTTPException(status_code=404, detail="File not found")

    return FileResponse(path)


@router.get("/download/{user_key}/{torrent_hash}")
async def download_stream(
    request: Request,
    torrent_service: Annotated[TorrentService, Depends()],
    file_service: Annotated[FileManager, Depends()],
    torrent_hash: str,
    tracker: str,
    api_key: str,
    season: Optional[int] = None,
    episode: Optional[int] = None,
):
    if tracker == "c411":
        torrent_url = f"https://c411.org/api?t=get&id={torrent_hash}&apikey={api_key}"
    else:
        raise HTTPException(status_code=400, detail="Invalid tracker")

    available_size = (
        request.state.user.transmission_data.size * 1024 * 1024 * 1024
        - await file_service.get_folder_size()
    )

    try:
        added_hash = await torrent_service.add_torrent(
            torrent=torrent_url, max_size=available_size
        )
        await torrent_service.wait_for_download_start(added_hash, timeout=15.0)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    user_key = request.state.user.api_key

    redirect_url = f"/streams/{user_key}?torrent_hash={added_hash}"

    if season and episode:
        redirect_url += f"&season={season}&episode={episode}"

    return RedirectResponse(url=redirect_url)
