# This file is AI-generated
import os
from collections.abc import AsyncGenerator

import asyncpg
import pytest
import pytest_asyncio

# ---------------------------------------------------------------------------
# Test database URL – MUST point at a separate database from dev/prod.
# The test suite never touches DATABASE_URL.
# ---------------------------------------------------------------------------
TEST_DATABASE_URL = os.getenv("TEST_DATABASE_URL", "")

# ---------------------------------------------------------------------------
# DDL helpers
# ---------------------------------------------------------------------------

UUIDV7_FUNCTION_SQL = """
CREATE OR REPLACE FUNCTION uuidv7() RETURNS uuid AS $$
BEGIN
    RETURN gen_random_uuid();
END;
$$ LANGUAGE plpgsql;
"""

USERS_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS public.users (
    id uuid DEFAULT uuidv7() NOT NULL,
    created_at timestamp without time zone DEFAULT now() NOT NULL,
    c411_key character varying(255),
    torr9_key character varying(255),
    lacale_key character varying(255),
    librebox_url character varying(255) NOT NULL,
    librebox_token character varying(255) NOT NULL,
    CONSTRAINT users_pkey PRIMARY KEY (id)
);
"""


async def _setup_test_db(conn: asyncpg.Connection) -> None:
    """Create the minimal schema required by UserService."""
    # pgcrypto provides gen_random_uuid() used by our uuidv7() stub.
    await conn.execute("CREATE EXTENSION IF NOT EXISTS pgcrypto")
    await conn.execute(UUIDV7_FUNCTION_SQL)
    await conn.execute(USERS_TABLE_SQL)


async def _clean_users_table(conn: asyncpg.Connection) -> None:
    """Truncate the users table so each test starts with a clean slate."""
    await conn.execute("TRUNCATE TABLE public.users RESTART IDENTITY CASCADE")


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest_asyncio.fixture(scope="session")
async def pg_pool() -> AsyncGenerator[asyncpg.Pool, None]:
    """Session-scoped pool connected to the test database."""
    if not TEST_DATABASE_URL:
        pytest.fail("TEST_DATABASE_URL is not set – cannot connect to a test database.")

    pool = await asyncpg.create_pool(dsn=TEST_DATABASE_URL, min_size=1, max_size=5)

    # Ensure the schema exists once per test session.
    async with pool.acquire() as conn:
        await _setup_test_db(conn)

    yield pool

    await pool.close()


@pytest_asyncio.fixture()
async def conn(pg_pool: asyncpg.Pool) -> AsyncGenerator[asyncpg.Connection, None]:
    """Function-scoped connection with automatic cleanup of the users table."""
    async with pg_pool.acquire() as connection:
        # Clean up *before* the test to avoid "operation in progress" races
        # that can occur when cleaning up after yield inside pool.acquire().
        await _clean_users_table(connection)
        yield connection
