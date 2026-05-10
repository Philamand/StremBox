from typing import Annotated

from fastapi.responses import FileResponse, HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from config import BASE_URL, HANKO_URL
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Request
from services.files import FileManager
from utils.auth import require_auth
from utils.files import zip_directory
from utils.htmx import is_htmx_request
from utils.jinja_filters import register_filters

router = APIRouter(prefix="/files")
templates = Jinja2Templates(directory="templates")
register_filters(templates.env)


@router.get("/", dependencies=[Depends(require_auth)])
async def list_files(
    request: Request,
    is_htmx: Annotated[bool, Depends(is_htmx_request)],
    file_manager: Annotated[FileManager, Depends()],
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
        {
            "hanko_url": HANKO_URL,
            "files": files,
            "folder": folder,
            "is_htmx": is_htmx,
        },
    )


@router.get("/download")
async def download_file(
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
        return RedirectResponse(f"{BASE_URL}/files/{file_path}.zip")
    return FileResponse(path)


@router.delete("/", dependencies=[Depends(require_auth)])
async def delete_file(
    file_path: str,
    file_manager: Annotated[FileManager, Depends()],
):
    try:
        await file_manager.remove_file(file_path)
    except Exception:
        raise HTTPException(status_code=404, detail="Fichier non trouvé")
    return {"message": "Fichier supprimé avec succès"}
