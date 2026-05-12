from typing import Annotated

from fastapi import APIRouter, Depends, File, Form, Request, UploadFile
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from services.files import FileManager
from services.torrents import TorrentService
from utils.auth import require_auth
from utils.htmx import is_htmx_request
from utils.jinja_filters import register_filters

dashboard_router = APIRouter(dependencies=[Depends(require_auth)])
templates = Jinja2Templates(directory="templates")
register_filters(templates.env)


@dashboard_router.get("/")
async def dashboard(
    request: Request,
    is_htmx: Annotated[bool, Depends(is_htmx_request)],
    torrent_service: Annotated[TorrentService, Depends()],
) -> HTMLResponse:
    """Render the dashboard page, showing the user's torrent list."""
    if is_htmx:
        template = "components/torrent_list.html"
    else:
        template = "dashboard.html"

    torrent_list = await torrent_service.get_torrents()
    torrent_list = sorted(
        torrent_list, key=lambda torrent: torrent.added_date, reverse=True
    )

    return templates.TemplateResponse(
        request,
        template,
        {"torrent_list": torrent_list},
    )


@dashboard_router.post("/")
async def add_torrent(
    request: Request,
    torrent_service: Annotated[TorrentService, Depends()],
    file_service: Annotated[FileManager, Depends()],
    torrent_file: UploadFile | None = File(None),
    torrent_magnet: str | None = Form(None),
) -> HTMLResponse:
    """Add a torrent to the user's list, either from a file or a magnet link."""
    if torrent_magnet:
        data = torrent_magnet
    elif torrent_file:
        data = await torrent_file.read()
    else:
        return templates.TemplateResponse(
            request,
            "components/error_alert.html",
            {"message": "Veuillez sélectionner un fichier ou une URL magnet."},
            status_code=400,
        )

    available_size = (
        request.state.user.transmission_data.size * 1024 * 1024 * 1024
        - await file_service.get_folder_size()
    )

    try:
        await torrent_service.add_torrent(data, available_size)
    except ValueError as e:
        return templates.TemplateResponse(
            request,
            "components/error_alert.html",
            {"message": str(e)},
            status_code=400,
        )

    return templates.TemplateResponse(
        request,
        "components/upload_modal_box.html",
    )


@dashboard_router.delete("/{hash}")
async def delete_torrent(
    hash: str,
    torrent_service: Annotated[TorrentService, Depends()],
    delete_files: bool = False,
):
    """Delete a torrent by hash."""
    await torrent_service.remove_torrent(hash, delete_files=delete_files)
    return {"message": "Torrent supprimé avec succès"}
