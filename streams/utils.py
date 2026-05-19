import asyncio
import os
import re
from typing import Optional, Tuple

import aiofiles
from fastapi import Request

# Video file extensions and their MIME types
VIDEO_MIME_TYPES = {
    ".mp4": "video/mp4",
    ".mkv": "video/x-matroska",
    ".webm": "video/webm",
    ".avi": "video/x-msvideo",
    ".mov": "video/quicktime",
    ".flv": "video/x-flv",
    ".wmv": "video/x-ms-wmv",
    ".m3u8": "application/vnd.apple.mpegurl",
    ".ts": "video/mp2t",
    ".mpg": "video/mpeg",
    ".mpeg": "video/mpeg",
    ".3gp": "video/3gpp",
    ".ogv": "video/ogg",
}


def parse_range(header: Optional[str]) -> Tuple[Optional[int], Optional[int]]:
    """
    Parse an HTTP Range header string into start and end byte offsets.

    This function expects a header value in the format 'bytes=start-end', where
    either start or end (or both) may be omitted to indicate an open-ended
    range. It validates that the unit is 'bytes' and attempts to convert the
    numeric parts to integers.

    Args:
        header: The raw Range header string, e.g., "bytes=0-499" or "bytes=500-".

    Returns:
        A tuple (start, end) where each element is either an integer offset or
        None. Returns (None, None) if the header is empty, malformed, uses a
        non-bytes unit, or contains invalid numeric values.

    Examples:
        >>> parse_range("bytes=0-499")
        (0, 499)
        >>> parse_range("bytes=500-")
        (500, None)
        >>> parse_range("bytes=-100")
        (None, 100)
        >>> parse_range("bytes=")
        (None, None)
        >>> parse_range("invalid")
        (None, None)
    """
    if not header:
        return None, None
    try:
        unit, spec = header.split("=")
        if unit.lower() != "bytes":
            return None, None
        start_s, end_s = spec.split("-")
        start = int(start_s) if start_s else None
        end = int(end_s) if end_s else None
        return start, end
    except Exception:
        return None, None


async def range_file_reader(
    request: Request, filepath, start, end=None, chunk_size=256 * 1024
):
    """Read a file in byte ranges using chunked reading for memory efficiency."""
    if await request.is_disconnected():
        return
    try:
        async with aiofiles.open(filepath, "rb") as f:
            await f.seek(start)
            remaining = (end - start + 1) if end is not None else None
            while True:
                if await request.is_disconnected():
                    break
                if remaining is not None and remaining <= 0:
                    break
                to_read = (
                    min(chunk_size, remaining) if remaining is not None else chunk_size
                )
                data = await f.read(to_read)
                if not data:
                    break
                yield data
                if remaining is not None:
                    remaining -= len(data)
    except asyncio.CancelledError, ConnectionError:
        pass


def check_season_episode(name: str, target_season: int, target_episode: int) -> bool:
    """Checks if the torrent matches the target season/episode."""
    if target_season is None:
        return True

    name_upper = name.upper()

    se_pattern = re.compile(
        r"(?:S|SAISON|SEASON)[ ._-]?(\d{1,2})(?:[ ._-]?E(\d{1,2}))(?:(?:[ ._-]*(?:E|-|~)[ ._-]*)(\d{1,2}))?",
        re.IGNORECASE,
    )
    matches = se_pattern.findall(name_upper)

    if not matches:
        x_pattern = re.compile(r"(\d{1,2})x(\d{1,2})", re.IGNORECASE)
        matches = [(m[0], m[1], None) for m in x_pattern.findall(name_upper)]

    if not matches:
        s_only_pattern = re.compile(
            r"(?:S|SAISON|SEASON)[ ._-]?(\d{1,2})", re.IGNORECASE
        )
        matches = [(m, None, None) for m in s_only_pattern.findall(name_upper)]

    if not matches:
        return False

    for s, e_start, e_end in matches:
        try:
            season = int(s)
            if season != target_season:
                continue

            if e_start is None:
                return True

            start = int(e_start)
            end = int(e_end) if e_end else start

            if start <= target_episode <= end:
                return True

        except ValueError:
            continue

    return False


def parse_stream_hash(raw_hash: str) -> Tuple[str, Optional[int], Optional[int]]:
    """Split a composite stream hash into its base hash and optional season/episode.

    Args:
        raw_hash: A hash string, optionally suffixed with season and episode
            separated by colons, e.g. ``"abc123:1:5"``.

    Returns:
        A tuple ``(base_hash, season, episode)`` where ``season`` and
        ``episode`` are ``None`` when no suffix is present.
    """
    parts = raw_hash.split(":")
    if len(parts) > 1:
        return parts[0], int(parts[1]), int(parts[2])
    return raw_hash, None, None


def resolve_file_path(
    torrent_file: str, base_dir: str, season: Optional[int], episode: Optional[int]
) -> str:
    """Resolve the path (relative to ``BASE_DIR``) for the requested file.

    For plain files, validates that the file exists on disk and returns
    ``torrent_file`` unchanged.  For season/episode requests, scans the
    directory named ``torrent_file`` and returns the first matching entry.

    Args:
        torrent_file: File or directory name under ``BASE_DIR``.
        base_dir: The base directory to resolve relative paths against.
        season: Target season number, or ``None`` for non-series files.
        episode: Target episode number, or ``None`` for non-series files.

    Returns:
        Relative path under ``BASE_DIR`` for the resolved media file.

    Raises:
        HTTPException 404: When the directory or matching episode file is not found.
    """
    from fastapi import HTTPException

    if season is not None and episode is not None:
        dir_path = base_dir + os.path.dirname(torrent_file)
        if not os.path.isdir(dir_path):
            raise HTTPException(status_code=404)
        for f in os.listdir(dir_path):
            if check_season_episode(f, season, episode):
                return dir_path + "/" + f
        raise HTTPException(status_code=404)

    if not os.path.isfile(base_dir + torrent_file):
        raise HTTPException(status_code=404)

    return torrent_file


def build_stream_headers(
    file_path: str, file_range: Optional[str], start: int, end: int, size: int
) -> Tuple[dict, int]:
    """Build HTTP response headers and status code for a streaming response.

    Args:
        file_path: Path to the video file being streamed.
        file_range: The raw ``Range`` header value from the request, or ``None``.
        start: Inclusive start byte offset.
        end: Inclusive end byte offset.
        size: Total file size in bytes.

    Returns:
        A tuple ``(headers, status_code)`` ready to pass to
        :class:`~fastapi.responses.StreamingResponse`.

    Raises:
        ValueError: If the file is not a supported video format.
    """

    file_ext = os.path.splitext(file_path)[1].lower()

    if file_ext not in VIDEO_MIME_TYPES:
        raise ValueError(
            f"Unsupported file format '{file_ext}'. Supported formats: {', '.join(VIDEO_MIME_TYPES.keys())}"
        )

    content_type = VIDEO_MIME_TYPES[file_ext]

    headers: dict = {
        "accept-ranges": "bytes",
        "content-type": content_type,
    }
    if file_range is not None:
        headers["content-range"] = f"bytes {start}-{end}/{size}"
        headers["content-length"] = str(end - start + 1)
        return headers, 206
    headers["content-length"] = str(size)
    return headers, 200
