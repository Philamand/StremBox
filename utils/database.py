from contextlib import asynccontextmanager

import aiosqlite

from config import DATABASE_URL


class AsyncDatabase:
    """Async SQLite database utility."""

    def __init__(self, db_path: str = DATABASE_URL):
        self.db_path = db_path

    @asynccontextmanager
    async def connection(self):
        """Context manager for getting a database connection."""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            try:
                yield db
            finally:
                await db.close()

    async def execute(self, query: str, params: tuple = ()):
        """Execute a query and return the cursor."""
        async with self.connection() as db:
            return await db.execute(query, params)

    async def fetch_one(self, query: str, params: tuple = ()):
        """Fetch a single row."""
        async with self.connection() as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute(query, params)
            return await cursor.fetchone()

    async def fetch_all(self, query: str, params: tuple = ()):
        """Fetch all rows."""
        async with self.connection() as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute(query, params)
            return await cursor.fetchall()

    async def commit_execute(self, query: str, params: tuple = ()):
        """Execute a query and commit the transaction."""
        async with self.connection() as db:
            await db.execute(query, params)
            await db.commit()
