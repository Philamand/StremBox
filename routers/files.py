from typing import Annotated

from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from config import HANKO_URL
from services.files import FileManager
from utils.auth import get_user
from utils.htmx import is_htmx_request
from utils.jinja_filters import register_filters

router = APIRouter()
templates = Jinja2Templates(directory="templates")
register_filters(templates.env)


@router.get("/")
async def list_files(
    request: Request,
    is_htmx: Annotated[bool, Depends(is_htmx_request)],
    file_manager: Annotated[FileManager, Depends()],
    folder: str | None = None,
    user: str = Depends(get_user),
) -> HTMLResponse:
    """Return the list of files from the configured directory."""
    files = await file_manager.list_files(folder)
    if is_htmx:
        template = "components/file_list.html"
    else:
        template = "files.html"
    return templates.TemplateResponse(
        request,
        template,
        {"hanko_url": HANKO_URL, "user": user, "files": files, "folder": folder},
    )
