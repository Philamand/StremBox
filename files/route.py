from typing import Annotated

from aiofiles import open as aopen
from fastapi import (
    APIRouter,
    BackgroundTasks,
    Depends,
    HTTPException,
    Request,
    Response,
    UploadFile,
)
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.templating import Jinja2Templates

from core.htmx import is_htmx_request
from core.jinja_filters import register_filters
from files.services import FileManagerDep, UnzipServiceDep, ZipDirectoryServiceDep
from files.utils import unzip_archive, zip_directory
from torrents.services import TorrentServiceDep
from users.dependencies import require_auth

router = APIRouter(prefix="/files", dependencies=[Depends(require_auth)])
templates = Jinja2Templates(directory="templates")
register_filters(templates.env)

HtmxDep = Annotated[bool, Depends(is_htmx_request)]


@router.get("/")
async def list_files(
    request: Request,
    is_htmx: HtmxDep,
    file_manager: FileManagerDep,
    folder: str | None = None,
) -> HTMLResponse:
    """Return the list of files from the configured directory."""
    files = await file_manager.list_files(folder)
    size = await file_manager.get_folder_size()

    parent_folder = None
    if folder:
        parts = folder.split("/")
        parent_folder = "/".join(parts[:-1]) if len(parts) > 1 else None

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
            "parent_folder": parent_folder,
            "is_htmx": is_htmx,
            "size": size,
            "total_size": request.state.user.transmission_data.size,
        },
    )


@router.get("/status/{zip_id}")
async def get_zip_status(
    request: Request,
    zip_id: int,
    zip_service: ZipDirectoryServiceDep,
) -> Response:
    """Return the status of a zip file by ID."""
    try:
        zip = await zip_service.get_zip(zip_id)
    except LookupError:
        return Response(status_code=404)
    if zip.done is True:
        return templates.TemplateResponse(
            request,
            "components/zip_modal_box.html",
            {"path": zip.path},
            headers={"HX-Reswap": "outerHTML"},
        )
    return Response(status_code=200)


@router.get("/unzip/status/{unzip_id}")
async def get_unzip_status(
    request: Request,
    unzip_id: int,
    unzip_service: UnzipServiceDep,
) -> Response:
    """Return the status of an extraction by ID."""
    try:
        extraction = await unzip_service.get_extraction(unzip_id)
    except LookupError:
        return Response(status_code=404)
    if extraction.done is True:
        Response(status_code=200, headers={"HX-Refresh": "true"})
    return Response(status_code=200)


@router.post("/unzip")
async def unzip_archive_route(
    request: Request,
    file_path: str,
    file_manager: FileManagerDep,
    unzip_service: UnzipServiceDep,
    background_tasks: BackgroundTasks,
) -> Response:
    """
    Initiate extraction of an archive file.
    """
    import os as _pyos

    source_path = file_manager.get_path(file_path)

    if not await file_manager.exists(source_path):
        return templates.TemplateResponse(
            request,
            "components/error_alert.html",
            {"message": "Archive introuvable."},
            status_code=404,
        )

    available_size = (
        request.state.user.transmission_data.size * 1024 * 1024 * 1024
        - await file_manager.get_folder_size()
    )

    try:
        archive_size = await file_manager.get_size(source_path)
    except OSError:
        archive_size = 0

    if available_size < archive_size:
        return templates.TemplateResponse(
            request,
            "components/error_alert.html",
            {"message": "Espace insuffisant pour extraire cette archive."},
            status_code=400,
        )

    base_name = _pyos.path.splitext(_pyos.path.basename(file_path))[0]
    dir_name = _pyos.path.dirname(file_path)
    destination_folder = f"{dir_name}/{base_name}" if dir_name else base_name
    destination_path = file_manager.get_path(destination_folder)

    if await file_manager.exists(destination_path):
        return templates.TemplateResponse(
            request,
            "components/error_alert.html",
            {"message": "Un dossier avec ce nom existe déjà."},
            status_code=400,
        )

    try:
        unzip_id = await unzip_service.create_extraction(file_path, destination_folder)
    except RuntimeError:
        raise HTTPException(400, "Erreur lors de la création de la tâche")

    background_tasks.add_task(
        unzip_archive, source_path, destination_path, unzip_id, unzip_service
    )

    return templates.TemplateResponse(
        request,
        "components/unzip_modal.html",
        {"unzip_id": unzip_id},
    )


@router.get("/download")
async def download_file(
    request: Request,
    file_path: str,
    file_manager: FileManagerDep,
    zip_service: ZipDirectoryServiceDep,
    background_tasks: BackgroundTasks,
) -> Response:
    """
    Download a file or a directory
    """
    path = file_manager.get_path(file_path)
    is_dir = await file_manager.is_dir(path)
    if is_dir:
        exists = await file_manager.exists(path + ".zip")
        if not exists:
            available_size = (
                request.state.user.transmission_data.size * 1024 * 1024 * 1024
                - await file_manager.get_folder_size()
                - await file_manager.get_folder_size(path)
            )

            if available_size < 0:
                return templates.TemplateResponse(
                    request,
                    "components/zip_modal.html",
                    {"path": file_path + ".zip"},
                )

            try:
                zip_id = await zip_service.create_zip(file_path + ".zip")
            except RuntimeError:
                raise HTTPException(400, "Une erreur est survenue")
            background_tasks.add_task(zip_directory, path, zip_id, zip_service)
            return templates.TemplateResponse(
                request,
                "components/zip_modal.html",
                {"zip_id": zip_id},
            )
        return templates.TemplateResponse(
            request,
            "components/zip_modal.html",
            {"path": file_path + ".zip"},
        )
    return FileResponse(path)


@router.post("/")
async def upload_file(
    request: Request,
    file_manager: FileManagerDep,
    uploaded_file: UploadFile | None = None,
    folder: str | None = None,
) -> Response:
    """Upload a file to the user's folder if there is enough space."""
    if uploaded_file is None:
        return templates.TemplateResponse(
            request,
            "components/error_alert.html",
            {"message": "Veuillez sélectionner un fichier."},
            status_code=400,
        )

    available_size = (
        request.state.user.transmission_data.size * 1024 * 1024 * 1024
        - await file_manager.get_folder_size()
    )

    content = await uploaded_file.read()
    if len(content) > available_size:
        return templates.TemplateResponse(
            request,
            "components/error_alert.html",
            {"message": "Espace insuffisant pour uploader ce fichier."},
            status_code=400,
        )

    dest_path = file_manager.get_path(uploaded_file.filename)
    async with aopen(dest_path, "wb") as f:
        await f.write(content)

    files = await file_manager.list_files(folder)
    size = await file_manager.get_folder_size()

    parent_folder = None
    if folder:
        parts = folder.split("/")
        parent_folder = "/".join(parts[:-1]) if len(parts) > 1 else None

    headers = {"HX-Reswap": "innerHTML"}

    return templates.TemplateResponse(
        request,
        "components/file_list.html",
        {
            "files": files,
            "folder": folder,
            "parent_folder": parent_folder,
            "is_htmx": True,
            "size": size,
            "total_size": request.state.user.transmission_data.size,
        },
        headers=headers,
    )


@router.delete("/")
async def delete_file(
    file_path: str,
    file_manager: FileManagerDep,
    torrent_service: TorrentServiceDep,
    background_tasks: BackgroundTasks,
) -> dict[str, str]:
    try:
        await file_manager.remove_file(file_path)
        background_tasks.add_task(torrent_service.verify_torrents_by_file, file_path)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Fichier non trouvé")
    return {"message": "Fichier supprimé avec succès"}
