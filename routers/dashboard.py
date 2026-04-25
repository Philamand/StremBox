from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from config import HANKO_URL
from services.torrent_manager import TorrentManager
from utils.auth import get_user
from utils.jinja_filters import register_filters

dashboard_router = APIRouter()
templates = Jinja2Templates(directory="templates")
register_filters(templates.env)


@dashboard_router.get("/")
async def dashboard(
    request: Request,
    user: str = Depends(get_user),
    torrent_manager: TorrentManager = Depends(),
) -> HTMLResponse:
    torrent_list = await torrent_manager.get_torrent_list()

    return templates.TemplateResponse(
        request=request,
        name="dashboard.html",
        context={"hanko_url": HANKO_URL, "user": user, "torrent_list": torrent_list},
    )


@dashboard_router.delete("/{hash}")
async def delete_torrent(
    hash: str,
    torrent_manager: TorrentManager = Depends(),
):
    """Delete a torrent by hash."""
    await torrent_manager.delete_torrent(hash)
    return {"message": "Torrent supprimé avec succès"}
