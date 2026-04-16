import json
import os
from contextlib import asynccontextmanager
from typing import AsyncGenerator, cast

import asyncpg
from fastapi import FastAPI

DATABASE_URL = os.getenv("DATABASE_URL")

_pool: asyncpg.Pool | None = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    FastAPI lifespan context manager.

    On startup this function creates a global asyncpg connection pool and registers
    JSON codecs so that PostgreSQL `json`/`jsonb` values are decoded to Python
    objects automatically. On shutdown it closes the pool cleanly.

    This should be passed to FastAPI(...) as the `lifespan` argument.

    Args:
        app: FastAPI instance (provided by FastAPI when running lifespan).
    """
    global _pool

    _pool = await asyncpg.create_pool(
        dsn=DATABASE_URL,
        init=register_json_codec,
        min_size=5,
        max_size=20,
        max_queries=500,
        max_inactive_connection_lifetime=60.0,
        timeout=15,
        command_timeout=60,
    )

    yield

    await _pool.close()
    _pool = None


async def register_json_codec(conn: asyncpg.Connection):
    """
    Register JSON and JSONB codecs on a connection.

    asyncpg can be instructed to decode Postgres `json` and `jsonb` types
    into Python objects using custom encoder/decoder functions. This helper
    registers codecs for the connection supplied by the pool.

    Args:
        conn: An active asyncpg.Connection instance.
    """

    await conn.set_type_codec(
        "json",
        encoder=json.dumps,
        decoder=json.loads,
        schema="pg_catalog",
        format="text",
    )
    await conn.set_type_codec(
        "jsonb",
        encoder=json.dumps,
        decoder=json.loads,
        schema="pg_catalog",
        format="text",
    )


def get_pool() -> asyncpg.Pool:
    """
    Return the global asyncpg pool.

    Raises:
        RuntimeError: If the pool is not initialized (lifespan not running).

    Returns:
        The initialized asyncpg.Pool instance.
    """
    if _pool is None:
        raise RuntimeError("Database pool not initialized. Lifespan not running?")
    return _pool


async def get_db_conn() -> AsyncGenerator[asyncpg.Connection, None]:
    """
    FastAPI dependency that yields a database connection from the pool.

    Use as a dependency in route handlers:
        async def handler(conn: asyncpg.Connection = Depends(get_db_conn)):
            await conn.fetch(...)

    Yields:
        An active asyncpg.Connection for the duration of the request.

    Raises:
        RuntimeError: If the pool is not initialized.
    """
    pool = get_pool()
    async with pool.acquire() as conn:
        yield cast(asyncpg.Connection, conn)
