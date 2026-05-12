import uuid
from typing import Annotated

from fastapi import Depends

from schemas.users import TransmissionData, UserData
from utils.database import AsyncDatabase


class UserService:
    """User service for managing user data."""

    def __init__(self, db: Annotated[AsyncDatabase, Depends()]):
        self.db = db

    async def get_user(
        self, id: str | None = None, api_key: str | None = None
    ) -> UserData | None:
        """Get an user by their ID or API key."""
        if id is None and api_key is None:
            return None

        if api_key is not None:
            user = await self.db.fetch_one(
                "SELECT users.id, users.created_at, users.api_key, transmission.port, transmission.download_folder, transmission.size FROM users LEFT JOIN transmission ON transmission.id = users.transmission_id WHERE users.api_key = ?",
                (api_key,),
            )
        else:
            user = await self.db.fetch_one(
                "SELECT users.id, users.created_at, users.api_key, transmission.port, transmission.download_folder, transmission.size FROM users LEFT JOIN transmission ON transmission.id = users.transmission_id WHERE users.id = ?",
                (id,),
            )

        if not user:
            return None

        transmission_data = (
            TransmissionData(
                port=user["port"],
                download_folder=user["download_folder"],
                size=user["size"],
            )
            if user["port"] is not None
            else None
        )
        user_data = UserData(
            id=user["id"],
            created_at=user["created_at"],
            api_key=user["api_key"],
            transmission_data=transmission_data,
        )

        return user_data

    async def get_user_list(self) -> list[UserData]:
        """Get a list of all users."""
        users = await self.db.fetch_all(
            "SELECT users.id, users.created_at, users.api_key, transmission.port, transmission.download_folder, transmission.size FROM users LEFT JOIN transmission ON transmission.id = users.transmission_id"
        )

        user_list = []
        for user in users:
            transmission_data = (
                TransmissionData(
                    port=user["port"],
                    download_folder=user["download_folder"],
                    size=user["size"],
                )
                if user["port"] is not None
                else None
            )
            user_data = UserData(
                id=user["id"],
                created_at=user["created_at"],
                api_key=user["api_key"],
                transmission_data=transmission_data,
            )
            user_list.append(user_data)

        return user_list

    async def delete_user(self, id: str) -> None:
        """Delete a user by ID."""
        await self.db.commit_execute(
            "DELETE FROM users WHERE id = ?",
            (id,),
        )

    async def create_user(self, id: str, transmission_id: int) -> None:
        """Create a new user."""
        api_key = str(uuid.uuid4())
        await self.db.commit_execute(
            "INSERT INTO users (id, api_key, transmission_id) VALUES (?, ?, ?)",
            (id, api_key, transmission_id),
        )
