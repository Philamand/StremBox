from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from config import HANKO_URL
from services.files import FileManager
from utils.auth import get_user
from utils.jinja_filters import register_filters

router = APIRouter()
templates = Jinja2Templates(directory="templates")
register_filters(templates.env)


@router.get("/")
async def list_files(
    request: Request,
    folder: str | None = None,
    user: str = Depends(get_user),
    file_manager: FileManager = Depends(),
) -> HTMLResponse:
    """Return the list of files from the configured directory."""
    files = await file_manager.list_files(folder)
    return templates.TemplateResponse(
        request,
        "files.html",
        {"hanko_url": HANKO_URL, "user": user, "files": files, "folder": folder},
    )
