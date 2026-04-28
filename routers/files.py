from typing import Annotated

from fastapi import APIRouter, BackgroundTasks, Depends, Request
from fastapi.responses import FileResponse, HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from config import HANKO_URL
from services.files import FileManager
from utils.auth import get_user
from utils.files import zip_directory
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
    user: Annotated[str, Depends(get_user)],
    folder: str | None = None,
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


@router.get("/{file_path}")
async def download_file(
    request: Request,
    file_path: str,
    file_manager: Annotated[FileManager, Depends()],
    background_tasks: BackgroundTasks,
):
    path = file_manager.get_path(file_path)
    is_dir = await file_manager.is_dir(path)
    if is_dir:
        exists = await file_manager.exists(path + ".zip")
        if not exists:
            background_tasks.add_task(zip_directory, path)
        return RedirectResponse("http://localhost:3000/files/" + file_path + ".zip")
    return FileResponse(path)
