import os
import re
from typing import Optional, Tuple

import aiofiles
from fastapi import Request

from config import BASE_DIR


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
    request: Request,
    filepath: str,
    start: int,
    end: Optional[int] = None,
    chunk_size: int = 256 * 1024,
):
    """Read a file in byte ranges using chunked reading for memory efficiency.

    This generator function reads a specified byte range from a file without
    loading the entire file into memory. It supports partial ranges
    (start-only, end-only, or both) and processes data in configurable chunks
    suitable for large files.

    Args:
        filepath: Path to the file to read.
        start: Starting byte offset (inclusive) from which to begin reading.
        end: Ending byte offset (inclusive). If None, reads to end of file.
        chunk_size: Number of bytes to read per iteration. Defaults to 256 KB.

    Yields:
        Bytes objects containing chunks of data from the specified range. Each
        chunk is at most chunk_size bytes, except possibly the last chunk which
        may be smaller.

    Raises:
        FileNotFoundError: If the file does not exist.
        PermissionError: If the file cannot be read due to permissions.
        OSError: For other file-related errors.

    Notes:
        - The end parameter is inclusive (unlike typical Python slicing).
        - If start exceeds file size, yields nothing.
        - If end exceeds file size, reads until EOF.
        - Uses binary mode ("rb") for precise byte-level control.
    """
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


def check_season_episode(name, target_season, target_episode):
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
    torrent_file: str, season: Optional[int], episode: Optional[int]
) -> str:
    """Resolve the path (relative to ``BASE_DIR``) for the requested file.

    For plain files, validates that the file exists on disk and returns
    ``torrent_file`` unchanged.  For season/episode requests, scans the
    directory named ``torrent_file`` and returns the first matching entry.

    Args:
        torrent_file: File or directory name under ``BASE_DIR``.
        season: Target season number, or ``None`` for non-series files.
        episode: Target episode number, or ``None`` for non-series files.

    Returns:
        Relative path under ``BASE_DIR`` for the resolved media file.

    Raises:
        HTTPException 404: When the directory or matching episode file is not found.
    """
    from fastapi import HTTPException

    torrent_file = "/" + torrent_file.split("/")[-1]

    if season is not None and episode is not None:
        dir_path = BASE_DIR + torrent_file
        if not os.path.isdir(dir_path):
            raise HTTPException(status_code=404)
        for f in os.listdir(dir_path):
            if check_season_episode(f, season, episode):
                return BASE_DIR + torrent_file + "/" + f
        raise HTTPException(status_code=404)

    if not os.path.isfile(BASE_DIR + torrent_file):
        print(BASE_DIR + torrent_file)
        raise HTTPException(status_code=404)
    return BASE_DIR + torrent_file


def build_stream_headers(
    file_range: Optional[str], start: int, end: int, size: int
) -> Tuple[dict, int]:
    """Build HTTP response headers and status code for a streaming response.

    Args:
        file_range: The raw ``Range`` header value from the request, or ``None``.
        start: Inclusive start byte offset.
        end: Inclusive end byte offset.
        size: Total file size in bytes.

    Returns:
        A tuple ``(headers, status_code)`` ready to pass to
        :class:`~fastapi.responses.StreamingResponse`.
    """
    headers: dict = {
        "accept-ranges": "bytes",
        "content-type": "video/x-matroska",
    }
    if file_range is not None:
        headers["content-range"] = f"bytes {start}-{end}/{size}"
        headers["content-length"] = str(end - start + 1)
        return headers, 206
    headers["content-length"] = str(size)
    return headers, 200
