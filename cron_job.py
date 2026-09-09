#!/usr/bin/env python3
"""Cron job script for Trakt integration."""

import asyncio
import os

import asyncpg

from services.users import UserService

DATABASE_URL = os.getenv("DATABASE_URL")


async def main():
    """Main cron job logic."""
    pool = await asyncpg.create_pool(
        dsn=DATABASE_URL,
        min_size=1,
        max_size=5,
    )

    try:
        async with pool.acquire() as conn:
            user_service = UserService(conn)
            users = await user_service.get_all_users(filter_without_trakt_slug=True)
            print(f"Found {len(users)} users without Trakt slug")

    finally:
        await pool.close()


if __name__ == "__main__":
    asyncio.run(main())
