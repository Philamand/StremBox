import asyncio
import os

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import StreamingResponse

from services.torrent_manager import TorrentManager
from utils.streams import (
    build_stream_headers,
    parse_range,
    parse_stream_hash,
    range_file_reader,
    resolve_file_path,
)

router = APIRouter()


@router.get("/{hash}")
async def get_stream(
    hash: str,
    request: Request,
    tracker: str | None = None,
    torrent_manager: TorrentManager = Depends(),
):
    file_range = request.headers.get("range")

    hash, season, episode = parse_stream_hash(hash)

    torrent_exists = await asyncio.to_thread(torrent_manager.check_torrent, hash)

    if not torrent_exists:
        if not tracker:
            raise HTTPException(status_code=404, detail="Torrent introuvable")
        await asyncio.to_thread(torrent_manager.add_torrent, hash, tracker)
        await asyncio.to_thread(torrent_manager.wait_until_added, hash)

    torrent_files = await asyncio.to_thread(torrent_manager.get_torrent_files, hash)

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
