import asyncio
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import (
    FileResponse,
    RedirectResponse,
    Response,
    StreamingResponse,
)

from files.services import FileManager
from streams.utils import (
    build_stream_headers,
    build_stream_response,
    range_file_reader,
    resolve_file_path,
)
from torrents.services import TorrentService
from users.security import check_user_key


def get_file_manager(request: Request) -> FileManager:
    return FileManager(request)


FileManagerDep = Annotated[FileManager, Depends(get_file_manager)]


def get_torrent_service(request: Request) -> TorrentService:
    return TorrentService(request)


TorrentServiceDep = Annotated[TorrentService, Depends(get_torrent_service)]

router = APIRouter(prefix="/streams", dependencies=[Depends(check_user_key)])


@router.get("/{user_key}")
async def get_stream(
    request: Request,
    file_manager: FileManagerDep,
    file_path: Annotated[str | None, Query()] = None,
) -> StreamingResponse:
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
    file_manager: FileManagerDep,
    file_path: Annotated[str | None, Query()] = None,
) -> Response:
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
    torrent_service: TorrentServiceDep,
    file_service: FileManagerDep,
    torrent_hash: str,
    torrent_url: Annotated[str | None, Query()] = None,
    season: Annotated[int | None, Query()] = None,
    episode: Annotated[int | None, Query()] = None,
):
    try:
        await torrent_service.get_torrent(torrent_hash)
    except KeyError:
        if not torrent_url:
            raise HTTPException(status_code=400, detail="Invalid tracker")

        available_size = (
            request.state.user.transmission_data.size * 1024 * 1024 * 1024
            - await file_service.get_folder_size()
        )

        try:
            await torrent_service.add_torrent(
                torrent=torrent_url, max_size=available_size
            )
            await torrent_service.wait_for_download_start(
                torrent_hash, timeout=60.0, min_percent=0.01
            )

        except ValueError as e:
            raise HTTPException(status_code=500, detail=str(e))

    torrent_files = await torrent_service.get_torrent_files(torrent_hash)
    file_path = await asyncio.to_thread(
        resolve_file_path,
        torrent_files[0].name,
        request.state.user.transmission_data.download_folder,
        season,
        episode,
        False,
    )

    referer = request.headers.get("referer", None)

    if referer is not None and referer == "https://web.stremio.com/":
        return RedirectResponse(url=f"/static/{file_path}")

    file_path = f"{request.state.user.transmission_data.download_folder}/{file_path}"
    return FileResponse(file_path)
