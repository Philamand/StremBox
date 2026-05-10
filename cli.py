import asyncio

import typer

from services.transmission import TransmissionService
from services.users import UserService
from utils.database import AsyncDatabase

app = typer.Typer()


@app.command()
def user_add(
    id: str,
    transmission_id: int,
):
    """Add a new user with the specified ID and transmission ID."""
    db = AsyncDatabase()
    user_service = UserService(db)
    asyncio.run(user_service.create_user(id, transmission_id))
    typer.echo("Utilisateur créé avec succès.")


@app.command()
def transmission_add(
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
