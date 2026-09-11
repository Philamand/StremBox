import asyncio
import os

import asyncpg

from services.bauxite import BauxiteService
from services.stremio import C411Service, StremioOrchestrationService, Tr4kerService
from services.trakt import TraktService
from services.users import UserService

DATABASE_URL = os.getenv("DATABASE_URL")


async def main():
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
                bauxite_service = BauxiteService(user.librebox_url, user.librebox_token)
                hashes = await bauxite_service.get_torrent_hashes()

                if user.trakt_slug:
                    if user.c411_key:
                        c411_service = C411Service(user.c411_key)
                    else:
                        c411_service = None

                    if user.tr4ker_key:
                        tr4ker_service = Tr4kerService(user.tr4ker_key)
                    else:
                        tr4ker_service = None

                    stremio_service = StremioOrchestrationService(
                        user.librebox_url,
                        user.librebox_token,
                        c411_service=c411_service,
                        tr4ker_service=tr4ker_service,
                    )

                    movies = await trakt_service.get_unwatched_movies(user.trakt_slug)
                    # shows = await trakt_service.get_unwatched_shows(user.trakt_slug)

                    for movie in movies:
                        in_library = False
                        results = await stremio_service.search_movie(
                            str(movie.movie.ids.tmdb)
                        )

                        for result in results:
                            if result["info_hash"] in hashes:
                                in_library = True
                                break

                        if not in_library and len(results) > 0:
                            await bauxite_service.add_torrent_download(
                                results[0]["link"]
                            )

    finally:
        await pool.close()


if __name__ == "__main__":
    asyncio.run(main())
