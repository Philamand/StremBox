from typing import Any


def _bdecode(data: bytes, pos: int = 0) -> tuple[Any, int]:
    """Decode a single bencode value starting at *pos*.

    Returns ``(value, new_pos)`` where *new_pos* is the index of the first
    byte that was not consumed.
    """
    first = chr(data[pos])
    if first == "i":
        end = data.index(b"e", pos + 1)
        return int(data[pos + 1 : end]), end + 1
    elif first == "l":
        pos += 1
        result: list[Any] = []
        while chr(data[pos]) != "e":
            item, pos = _bdecode(data, pos)
            result.append(item)
        return result, pos + 1
    elif first == "d":
        pos += 1
        result_dict: dict[Any, Any] = {}
        while chr(data[pos]) != "e":
            key, pos = _bdecode(data, pos)
            val, pos = _bdecode(data, pos)
            result_dict[key] = val
        return result_dict, pos + 1
    else:
        colon = data.index(b":", pos)
        length = int(data[pos:colon])
        start = colon + 1
        return data[start : start + length], start + length


def get_torrent_size(torrent_data: bytes) -> int:
    """Return the total content size (in bytes) encoded in a .torrent file."""
    decoded, _ = _bdecode(torrent_data)
    info: dict[bytes, Any] = decoded[b"info"]
    if b"length" in info:
        return int(info[b"length"])
    return sum(int(f[b"length"]) for f in info[b"files"])
