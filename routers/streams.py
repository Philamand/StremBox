from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import FileResponse

from services.files import FileManager
from services.torrents import TorrentService
from utils.security import check_user_key

router = APIRouter(prefix="/streams", dependencies=[Depends(check_user_key)])


@router.get("/{user_key}")
async def get_stream(
    request: Request,
    file_manager: Annotated[FileManager, Depends()],
    file_path: str,
) -> FileResponse:
    """Return a stream of the file at the given path."""
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
        # TODO: Handle redirect to file stream
        torrent = await torrent_service.add_torrent(
            torrent=torrent_url, max_size=available_size
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
