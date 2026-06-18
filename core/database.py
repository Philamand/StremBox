from contextlib import asynccontextmanager
from typing import Annotated, AsyncIterator

import aiosqlite
from fastapi import Depends

from core.config import settings


class AsyncDatabase:
    """Async SQLite database utility."""

    def __init__(self, db_path: str = settings.fastapi_database_url):
        self.db_path = db_path

    @asynccontextmanager
    async def connection(self) -> AsyncIterator[aiosqlite.Connection]:
        """Context manager for getting a database connection."""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            yield db

    async def execute(self, query: str, params: tuple = ()) -> aiosqlite.Cursor:
        """Execute a query and return the cursor."""
        async with self.connection() as db:
            return await db.execute(query, params)

    async def fetch_one(self, query: str, params: tuple = ()) -> aiosqlite.Row | None:
        """Fetch a single row."""
        async with self.connection() as db:
            cursor = await db.execute(query, params)
            return await cursor.fetchone()

    async def fetch_all(self, query: str, params: tuple = ()) -> list[aiosqlite.Row]:
        """Fetch all rows."""
        async with self.connection() as db:
            cursor = await db.execute(query, params)
            return list(await cursor.fetchall())

    async def commit_execute(self, query: str, params: tuple = ()) -> None:
        """Execute a query and commit the transaction."""
        async with self.connection() as db:
            await db.execute(query, params)
            await db.commit()

    async def commit_fetch_one(
        self, query: str, params: tuple = ()
    ) -> aiosqlite.Row | None:
        """Execute a query, commit the transaction, and return the first row."""
        async with self.connection() as db:
            cursor = await db.execute(query, params)
            row = await cursor.fetchone()
            await db.commit()
            return row


AsyncDatabaseDep = Annotated[AsyncDatabase, Depends()]
