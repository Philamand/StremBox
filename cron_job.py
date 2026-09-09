#!/usr/bin/env python3
"""Cron job script for Trakt integration."""

import asyncio
import os

import asyncpg

from services.trakt import TraktService
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
            trakt_service = TraktService()

            for user in users:
                movies = await trakt_service.get_unwatched_movies(user.trakt_slug)
                shows = await trakt_service.get_unwatched_shows(user.trakt_slug)

    finally:
        await pool.close()


if __name__ == "__main__":
    asyncio.run(main())
