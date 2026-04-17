import asyncpg

from schemas.users import UserCreateData, UserData


class UserService:
    """Service for managing users."""

    def __init__(self, conn: asyncpg.Connection):
        self.conn = conn

    async def create_user(self, user: UserCreateData) -> str:
        """Create a new user and return the user's ID."""
        result = await self.conn.fetch(
            "INSERT INTO users (streamer_url, c411_key, torr9_key, lacale_key) VALUES ($1, $2, $3, $4) RETURNING id",
            user.streamer_url,
            user.c411_key,
            user.torr9_key,
            user.lacale_key,
        )
        return result[0]["id"]

    async def get_user(self, user_id: str) -> UserData:
        """Get a user by their ID."""
        result = await self.conn.fetch(
            "SELECT * FROM users WHERE id = $1",
            user_id,
        )
        return UserData(**result[0])
