import asyncio

import typer
from rich.console import Console
from rich.table import Table

from services.transmission import TransmissionService
from services.users import UserService
from utils.database import AsyncDatabase

console = Console()
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
    asyncio.run(transmission_service.create_transmission(port, download_folder))
    typer.echo("Transmission créée avec succès.")


@app.command()
def transmission_list():
    """List all transmissions."""
    db = AsyncDatabase()
    transmission_service = TransmissionService(db)
    transmission_list = asyncio.run(transmission_service.get_transmission_list())

    table = Table("id", "port", "download_folder")
    for transmission in transmission_list:
        table.add_row(
            str(transmission.id), str(transmission.port), transmission.download_folder
        )
    console.print(table)


@app.command()
def transmission_delete(id: int):
    """Delete a transmission by ID."""
    db = AsyncDatabase()
    transmission_service = TransmissionService(db)
    asyncio.run(transmission_service.delete_transmission(id))
    typer.echo(f"Transmission #{id} supprimée avec succès.")


if __name__ == "__main__":
    app()
