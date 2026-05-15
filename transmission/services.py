from typing import Annotated

from fastapi import Depends

from core.database import AsyncDatabase
from transmission.schemas import TransmissionData


class TransmissionService:
    """Transmission service for managing transmission data."""

    def __init__(self, db: Annotated[AsyncDatabase, Depends()]):
        self.db = db

    async def create_transmission(self, port: int, download_folder: str, size: int):
        """Create a new transmission."""
        await self.db.commit_execute(
            "INSERT INTO transmission (port, download_folder, size) VALUES (?, ?, ?)",
            (port, download_folder, size),
        )

    async def get_transmission_list(self) -> list[TransmissionData]:
        """Get a list of all transmissions."""
        rows = await self.db.fetch_all("SELECT * FROM transmission")
        return [TransmissionData(**row) for row in rows]

    async def delete_transmission(self, id: int):
        """Delete a transmission by ID."""
        await self.db.commit_execute("DELETE FROM transmission WHERE id = ?", (id,))
