from typing import Annotated

from fastapi import Depends
from utils.database import AsyncDatabase


class TransmissionService:
    """Transmission service for managing transmission data."""

    def __init__(self, db: Annotated[AsyncDatabase, Depends()]):
        self.db = db

    async def create_transmission(self, port: int, download_folder: str) -> int:
        """Create a new transmission and return its ID."""
        id = await self.db.fetch_one(
            "INSERT INTO transmission (port, download_folder) VALUES (?, ?) RETURNING id",
            (port, download_folder),
        )
        return id["id"]
