import os
from typing import Annotated

from fastapi.responses import StreamingResponse

from fastapi import APIRouter, Depends, HTTPException, Request
from services.torrents import TorrentService
from utils.streams import (
    build_stream_headers,
    parse_range,
    parse_stream_hash,
    range_file_reader,
    resolve_file_path,
)

router = APIRouter(prefix="/streams")


@router.get("/{hash}")
async def get_stream(
    hash: str,
    request: Request,
    torrent_service: Annotated[TorrentService, Depends()],
    tracker: str | None = None,
    api_key: str | None = None,
    torrent_id: str | None = None,
):
    """
    Stream a video file from a torrent hash.
    """
    file_range = request.headers.get("range")

    hash, season, episode = parse_stream_hash(hash)

    torrent_files = await torrent_service.get_torrent_files(hash)

    file_path = resolve_file_path(torrent_files[0].name, season, episode)
    file_size = os.path.getsize(file_path)

    start, end = parse_range(file_range)
    if start is None:
        start = 0
    if end is None or end >= file_size:
        end = file_size - 1

    try:
        headers, status_code = build_stream_headers(
            file_path, file_range, start, end, file_size
        )
    except ValueError:
        raise HTTPException(status_code=415, detail="Fichier non pris en charge")

    return StreamingResponse(
        range_file_reader(request, file_path, start, end),
        status_code=status_code,
        headers=headers,
        media_type=headers["content-type"],
    )
