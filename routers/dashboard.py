from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from config import HANKO_URL
from services.torrent_manager import TorrentManager
from utils.auth import get_user

dashboard_router = APIRouter()
templates = Jinja2Templates(directory="templates")


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
