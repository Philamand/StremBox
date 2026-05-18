import asyncio
from typing import Annotated, AsyncGenerator, Optional

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import RedirectResponse, StreamingResponse

from files.services import FileManager
from streams.utils import (
    build_stream_headers,
    parse_range,
    range_file_reader,
    resolve_file_path,
)
from torrents.services import TorrentService
from users.security import check_user_key

router = APIRouter(prefix="/streams", dependencies=[Depends(check_user_key)])


async def _stream_growing_file(
    path: str,
    torrent_hash: str,
    torrent_service: TorrentService,
) -> AsyncGenerator[bytes, None]:
    """Yield chunks of a file that is still being downloaded by Transmission.

    When the current end-of-file is reached, the generator polls
    Transmission.  If the torrent is still active it waits for more data
    to be written; otherwise it stops.
    """
    with open(path, "rb") as f:
        while True:
            chunk = f.read(64 * 1024)
            if chunk:
                yield chunk
            else:
                t = await torrent_service.get_torrent(torrent_hash)
                if t.left_until_done == 0:
                    return
                await asyncio.sleep(0.5)


@router.get("/{user_key}")
async def get_stream(
    request: Request,
    file_manager: Annotated[FileManager, Depends()],
    torrent_service: Annotated[TorrentService, Depends()],
    file_path: Optional[str] = None,
    torrent_hash: Optional[str] = None,
    season: Optional[int] = None,
    episode: Optional[int] = None,
):
    """Return a stream of the file at the given path."""
    if not file_path and not torrent_hash:
        raise HTTPException(
            status_code=400, detail="Either file_path or torrent_hash is required"
        )

    file_range = request.headers.get("range")

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

    file_size = file_manager.get_size(path)

    start, end = parse_range(file_range)
    if start is None:
        start = 0
    if end is None or end >= file_size:
        end = file_size - 1

    try:
        headers, status_code = build_stream_headers(
            path, file_range, start, end, file_size
        )
    except ValueError:
        raise HTTPException(status_code=415, detail="Fichier non pris en charge")

    return StreamingResponse(
        range_file_reader(request, path, start, end),
        status_code=status_code,
        headers=headers,
        media_type=headers["content-type"],
    )


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
        await torrent_service.wait_for_download_start(
            added_hash, timeout=15.0, min_percent=0.01
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    user_key = request.state.user.api_key

    redirect_url = f"/streams/{user_key}?torrent_hash={added_hash}"

    if season and episode:
        redirect_url += f"&season={season}&episode={episode}"

    return RedirectResponse(url=redirect_url)
