from typing import Annotated

from fastapi import Depends
from schemas.users import TransmissionData, UserData
from utils.database import AsyncDatabase


class UserService:
    """User service for managing user data."""

    def __init__(self, db: Annotated[AsyncDatabase, Depends()]):
        self.db = db

    async def get_user(self, id: str) -> UserData | None:
        """Get an user by their ID."""
        user = await self.db.fetch_one(
            "SELECT users.id, users.created_at, transmission.port, transmission.download_folder FROM users LEFT JOIN transmission ON transmission.id = users.transmission_id WHERE users.id = ?",
            (id,),
        )

        if not user:
            return None

        transmission_data = (
            TransmissionData(port=user["port"], download_folder=user["download_folder"])
            if user["port"] is not None
            else None
        )
        user_data = UserData(
            id=user["id"],
            created_at=user["created_at"],
            transmission_data=transmission_data,
        )

        return user_data

    async def create_user(self, id: str, transmission_id: int) -> None:
        """Create a new user."""
        await self.db.execute(
            "INSERT INTO users (id, transmission_id) VALUES (?, ?)",
            (id, transmission_id),
        )
