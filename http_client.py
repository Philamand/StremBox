import aiohttp

_session: aiohttp.ClientSession | None = None


async def init_http_session() -> None:
    """Create the application-wide aiohttp ClientSession.

    A single session is shared across every request so the underlying TCP
    connection pool is reused instead of being recreated for each call.
    Must be called from within the running event loop (e.g. from the FastAPI
    lifespan), as the session binds to the loop that creates it.
    """
    global _session
    _session = aiohttp.ClientSession(
        trust_env=True,
        connector=aiohttp.TCPConnector(limit=100, limit_per_host=10),
    )


async def close_http_session() -> None:
    """Close the global aiohttp ClientSession if one is open."""
    global _session
    if _session is not None:
        await _session.close()
        _session = None


def get_session() -> aiohttp.ClientSession:
    """Return the shared aiohttp ClientSession.

    Raises:
        RuntimeError: If the session has not been initialized (lifespan not running).

    Returns:
        The initialized aiohttp.ClientSession instance.
    """
    if _session is None:
        raise RuntimeError("HTTP session not initialized. Lifespan not running?")
    return _session
