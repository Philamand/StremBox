import asyncpg

from schemas.users import UserFormData


class UserService:
    """Service for managing users."""

    def __init__(self, conn: asyncpg.Connection):
        self.conn = conn

    async def create_user(self, user: UserFormData) -> str:
        """Create a new user and return the user's ID."""
        result = await self.conn.execute(
            "INSERT INTO users (qbit_host, qbit_port, qbit_user, qbit_pass, c411_key, torr9_key, lacale_key) VALUES ($1, $2, $3, $4, $5, $6, $7) RETURNING id",
            user.qbit_host,
            user.qbit_port,
            user.qbit_user,
            user.qbit_pass,
            user.c411_key,
            user.torr9_key,
            user.lacale_key,
        )
        return result
