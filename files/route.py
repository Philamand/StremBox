from typing import Annotated

from fastapi import (
    APIRouter,
    BackgroundTasks,
    Depends,
    HTTPException,
    Request,
    Response,
)
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.templating import Jinja2Templates

from core.htmx import is_htmx_request
from core.jinja_filters import register_filters
from files.services import FileManager, ZipDirectoryService
from files.utils import zip_directory
from users.dependencies import require_auth

router = APIRouter(prefix="/files", dependencies=[Depends(require_auth)])
templates = Jinja2Templates(directory="templates")
register_filters(templates.env)


@router.get("/")
async def list_files(
    request: Request,
    is_htmx: Annotated[bool, Depends(is_htmx_request)],
    file_manager: Annotated[FileManager, Depends()],
    folder: str | None = None,
) -> HTMLResponse:
    """Return the list of files from the configured directory."""
    files = await file_manager.list_files(folder)
    size = await file_manager.get_folder_size()
    if is_htmx:
        template = "components/file_list.html"
    else:
        template = "files.html"
    return templates.TemplateResponse(
        request,
        template,
        {
            "files": files,
            "folder": folder,
            "is_htmx": is_htmx,
            "size": size,
            "total_size": request.state.user.transmission_data.size,
        },
    )


@router.get("/status/{zip_id}")
async def get_zip_status(
    request: Request,
    zip_id: int,
    zip_service: Annotated[ZipDirectoryService, Depends()],
):
    """Return the status of a zip file by ID."""
    zip = await zip_service.get_zip(zip_id)
    if zip.done is True:
        return templates.TemplateResponse(
            request,
            "components/zip_modal_box.html",
            {"path": zip.path},
            headers={"HX-Reswap": "outerHTML"},
        )
    return Response(status_code=200)


@router.get("/download")
async def download_file(
    request: Request,
    file_path: str,
    file_manager: Annotated[FileManager, Depends()],
    zip_service: Annotated[ZipDirectoryService, Depends()],
    background_tasks: BackgroundTasks,
):
    path = file_manager.get_path(file_path)
    is_dir = await file_manager.is_dir(path)
    if is_dir:
        exists = await file_manager.exists(path + ".zip")
        if not exists:
            zip_id = await zip_service.create_zip(path + ".zip")
            background_tasks.add_task(zip_directory, path, zip_id, zip_service)
            return templates.TemplateResponse(
                request,
                "components/zip_modal.html",
                {"zip_id": zip_id},
            )
        return templates.TemplateResponse(
            request,
            "components/zip_modal.html",
            {"path": path + ".zip"},
        )
    return FileResponse(path)


@router.delete("/")
async def delete_file(
    file_path: str,
    file_manager: Annotated[FileManager, Depends()],
):
    try:
        await file_manager.remove_file(file_path)
    except Exception:
        raise HTTPException(status_code=404, detail="Fichier non trouvé")
    return {"message": "Fichier supprimé avec succès"}
