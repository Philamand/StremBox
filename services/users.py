import asyncpg

from schemas.users import UserCreateData, UserData


class UserService:
    """Service for managing users."""

    def __init__(self, conn: asyncpg.Connection):
        self.conn = conn

    async def create_user(self, user: UserCreateData) -> str:
        """Create a new user and return the user's ID."""
        result = await self.conn.fetch(
            "INSERT INTO users (librebox_url, librebox_token, c411_key, tr4ker_key, lacale_key) VALUES ($1, $2, $3, $4, $5) RETURNING id",
            user.librebox_url,
            user.librebox_token,
            user.c411_key,
            user.tr4ker_key,
            user.lacale_key,
        )
        return result[0]["id"]

    async def update_user(self, user_id: str, user: UserCreateData) -> None:
        """Update an existing user with the given data."""
        result = await self.conn.execute(
            "UPDATE users SET librebox_url = $1, librebox_token = $2, c411_key = $3, tr4ker_key = $4, lacale_key = $5 WHERE id = $6",
            user.librebox_url,
            user.librebox_token,
            user.c411_key,
            user.tr4ker_key,
            user.lacale_key,
            user_id,
        )

        if result == "UPDATE 0":
            raise ValueError("User not found")

    async def get_user(self, user_id: str) -> UserData:
        """Get a user by their ID."""
        result = await self.conn.fetch(
            "SELECT * FROM users WHERE id = $1",
            user_id,
        )

        if not result:
            raise ValueError("User not found")

        return UserData(**result[0])
