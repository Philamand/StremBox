from typing import Annotated, Optional

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import RedirectResponse, Response, StreamingResponse

from files.services import FileManager
from streams.utils import (
    build_stream_headers,
    build_stream_response,
    range_file_reader,
    resolve_file_path,
)
from torrents.services import TorrentService
from users.security import check_user_key

router = APIRouter(prefix="/streams", dependencies=[Depends(check_user_key)])


@router.get("/{user_key}")
async def get_stream(
    request: Request,
    file_manager: Annotated[FileManager, Depends()],
    file_path: Optional[str] = None,
):
    """Return a stream of the file at the given path."""
    if not file_path:
        raise HTTPException(status_code=400, detail="file_path is required")

    file_range = request.headers.get("range")

    path, start, end, file_size = await build_stream_response(
        file_manager, file_path, file_range
    )

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


@router.head("/{user_key}")
async def head_stream(
    request: Request,
    file_manager: Annotated[FileManager, Depends()],
    file_path: Optional[str] = None,
):
    """Return headers for the stream of the file at the given path."""
    if not file_path:
        raise HTTPException(status_code=400, detail="file_path is required")

    file_range = request.headers.get("range")

    path, start, end, file_size = await build_stream_response(
        file_manager, file_path, file_range
    )

    try:
        headers, status_code = build_stream_headers(
            path, file_range, start, end, file_size
        )
    except ValueError:
        raise HTTPException(status_code=415, detail="Fichier non pris en charge")

    return Response(
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
    torrent_id: Optional[int] = None,
    season: Optional[int] = None,
    episode: Optional[int] = None,
):
    try:
        await torrent_service.get_torrent(torrent_hash)
    except KeyError:
        if tracker == "c411":
            torrent_url = (
                f"https://c411.org/api?t=get&id={torrent_hash}&apikey={api_key}"
            )
        elif tracker == "torr9" and torrent_id:
            torrent_url = f"https://api.torr9.net/api/v1/rss/torrents/{torrent_id}/download?passkey={api_key}"
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
                added_hash, timeout=60, min_percent=0.01
            )
            torrent_files = await torrent_service.get_torrent_files(added_hash)
            file_path = resolve_file_path(
                torrent_files[0].name,
                "",
                season,
                episode,
            )
            if len(torrent_files) >= 1:
                file = file_path
            else:
                file = None
            await torrent_service.wait_for_download_complete(
                added_hash, timeout=600, file_name=file
            )

        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

        return RedirectResponse(
            url=f"/streams/{request.state.user.api_key}?file_path={file_path}"
        )
