from typing import Annotated

from fastapi import Depends
from schemas.users import User
from utils.database import AsyncDatabase


class UserService:
    """User service for managing user data."""

    def __init__(self, db: Annotated[AsyncDatabase, Depends()]):
        self.db = db

    async def get_user(self, id: str) -> User | None:
        """Get a user by their ID."""
        user = await self.db.fetch_one("SELECT * FROM users WHERE id = ?", (id,))

        if not user:
            return None

        return User(**user)
