from typing import Annotated

from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from fastapi import APIRouter, Depends, File, Form, HTTPException, Request, UploadFile
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
    torrent_service: Annotated[TorrentService, Depends()],
    torrent_file: UploadFile | None = File(None),
    torrent_magnet: str | None = Form(None),
):
    """Add a torrent file and redirect to dashboard."""
    if torrent_magnet:
        data = torrent_magnet
    elif torrent_file:
        data = await torrent_file.read()
    else:
        raise HTTPException(status_code=400)

    await torrent_service.add_torrent(data)

    return RedirectResponse(url="/", status_code=303)


@dashboard_router.delete("/{hash}")
async def delete_torrent(
    hash: str,
    torrent_service: Annotated[TorrentService, Depends()],
    delete_files: bool = False,
):
    """Delete a torrent by hash."""
    await torrent_service.remove_torrent(hash, delete_files=delete_files)
    return {"message": "Torrent supprimé avec succès"}
