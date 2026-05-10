import asyncio

import typer

from services.transmission import TransmissionService
from utils.database import AsyncDatabase

app = typer.Typer()


@app.command()
def add_transmission(
    port: int = 9091,
    download_folder: str = "downloads/",
):
    """Add a new transmission with the specified port and download folder."""
    db = AsyncDatabase()
    transmission_service = TransmissionService(db)
    transmission_id = asyncio.run(
        transmission_service.create_transmission(port, download_folder)
    )
    typer.echo(f"Transmission créée avec l'ID: {transmission_id}")


if __name__ == "__main__":
    app()
