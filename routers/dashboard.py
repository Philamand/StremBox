from typing import Annotated

from fastapi import APIRouter, Depends, Request, UploadFile
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from config import HANKO_URL
from services.torrent_manager import TorrentManager
from utils.auth import get_user
from utils.htmx import is_htmx_request
from utils.jinja_filters import register_filters

dashboard_router = APIRouter()
templates = Jinja2Templates(directory="templates")
register_filters(templates.env)


@dashboard_router.get("/")
async def dashboard(
    request: Request,
    is_htmx: Annotated[bool, Depends(is_htmx_request)],
    user: Annotated[str, Depends(get_user)],
    torrent_manager: Annotated[TorrentManager, Depends()],
) -> HTMLResponse:
    if is_htmx:
        template = "components/torrent_list.html"
    else:
        template = "dashboard.html"

    torrent_list = await torrent_manager.get_torrent_list()
    torrent_list = sorted(
        torrent_list, key=lambda torrent: torrent.added_on, reverse=True
    )

    return templates.TemplateResponse(
        request,
        template,
        {"hanko_url": HANKO_URL, "user": user, "torrent_list": torrent_list},
    )


@dashboard_router.post("/")
async def add_torrent(
    torrent_file: UploadFile,
    user: Annotated[str, Depends(get_user)],
    torrent_manager: Annotated[TorrentManager, Depends()],
):
    """Add a torrent file and redirect to dashboard."""
    torrent_content = await torrent_file.read()
    await torrent_manager.add_torrent_file(torrent_content)
    return RedirectResponse(url="/", status_code=303)


@dashboard_router.delete("/{hash}")
async def delete_torrent(
    hash: str,
    torrent_manager: Annotated[TorrentManager, Depends()],
    delete_files: bool = False,
):
    """Delete a torrent by hash."""
    await torrent_manager.delete_torrent(hash, delete_files=delete_files)
    return {"message": "Torrent supprimé avec succès"}
