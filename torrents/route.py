from typing import Annotated

from fastapi import (
    APIRouter,
    Depends,
    File,
    Form,
    HTTPException,
    Query,
    Request,
    Response,
    UploadFile,
)
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from core.htmx import is_htmx_request
from core.jinja_filters import register_filters
from files.services import FileManagerDep
from torrents.schemas import DownloadRequest
from torrents.services import TorrentServiceDep
from users.dependencies import require_auth
from users.security import validate_bearer_token

# ── Dashboard (torrent management) router ────────────────────────────────
dashboard_router = APIRouter(dependencies=[Depends(require_auth)])
templates = Jinja2Templates(directory="templates")
register_filters(templates.env)


def _sorted_by_date(torrent_list: list) -> list:
    """Sort torrents by added_date descending."""
    return sorted(torrent_list, key=lambda t: t.added_date, reverse=True)


@dashboard_router.get("/")
async def dashboard(
    request: Request,
    is_htmx: Annotated[bool, Depends(is_htmx_request)],
    torrent_service: TorrentServiceDep,
) -> HTMLResponse:
    """Render the dashboard page, showing the user's torrent list."""
    if is_htmx:
        template = "components/torrent_list.html"
    else:
        template = "dashboard.html"

    torrent_list = await torrent_service.get_torrents()
    torrent_list = _sorted_by_date(torrent_list)

    return templates.TemplateResponse(
        request,
        template,
        {"torrent_list": torrent_list},
    )


@dashboard_router.post("/")
async def add_torrent(
    request: Request,
    torrent_service: TorrentServiceDep,
    file_service: FileManagerDep,
    torrent_file: Annotated[UploadFile | None, File()] = None,
    torrent_magnet: Annotated[str | None, Form()] = None,
    torrent_start: Annotated[bool, Form()] = False,
) -> HTMLResponse:
    """Add a torrent to the user's list, either from a file or a magnet link."""
    if torrent_magnet:
        data = torrent_magnet
    elif torrent_file:
        data = await torrent_file.read()
    else:
        return templates.TemplateResponse(
            request,
            "components/error_alert.html",
            {"message": "Veuillez sélectionner un fichier ou une URL magnet."},
            status_code=400,
        )

    available_size = (
        request.state.user.transmission_data.size * 1024 * 1024 * 1024
        - await file_service.get_folder_size()
    )

    try:
        await torrent_service.add_torrent(data, available_size, torrent_start)
    except ValueError as e:
        return templates.TemplateResponse(
            request,
            "components/error_alert.html",
            {"message": str(e)},
            status_code=400,
        )

    return templates.TemplateResponse(
        request,
        "components/upload_modal_box.html",
    )


@dashboard_router.post("/{hash}/start")
async def start_torrent(
    request: Request,
    hash: str,
    torrent_service: TorrentServiceDep,
) -> HTMLResponse:
    """Start a torrent by hash."""
    await torrent_service.start_torrent(hash)

    torrent_list = await torrent_service.get_torrents()
    torrent_list = _sorted_by_date(torrent_list)

    return templates.TemplateResponse(
        request,
        "components/torrent_list.html",
        {"torrent_list": torrent_list},
    )


@dashboard_router.post("/{hash}/stop")
async def stop_torrent(
    request: Request,
    hash: str,
    torrent_service: TorrentServiceDep,
) -> HTMLResponse:
    """Stop a torrent by hash."""
    await torrent_service.stop_torrent(hash)

    torrent_list = await torrent_service.get_torrents()
    torrent_list = _sorted_by_date(torrent_list)

    return templates.TemplateResponse(
        request,
        "components/torrent_list.html",
        {"torrent_list": torrent_list},
    )


@dashboard_router.delete("/{hash}")
async def delete_torrent(
    hash: str,
    torrent_service: TorrentServiceDep,
    delete_files: Annotated[bool, Query()] = False,
) -> dict[str, str]:
    """Delete a torrent by hash."""
    await torrent_service.remove_torrent(hash, delete_files=delete_files)
    return {"message": "Torrent supprimé avec succès"}


# ── API router ───────────────────────────────────────────────────────────
api_router = APIRouter(prefix="/api", dependencies=[Depends(validate_bearer_token)])


@api_router.get("/hashes/")
async def get_hashes(
    torrent_service: TorrentServiceDep,
) -> dict[str, dict]:
    """Get all torrent hashes from Transmission."""
    torrents = await torrent_service.get_torrents()
    hashes_dict = {}
    for torrent in torrents:
        hashes_dict[torrent.hashString] = {
            "percent_done": torrent.percent_done,
            "files": [file.name for file in torrent.get_files()],
        }
    return hashes_dict


@api_router.post("/download/")
async def download_torrent(
    request: Request,
    torrent_service: TorrentServiceDep,
    file_service: FileManagerDep,
    download_request: DownloadRequest,
) -> Response:
    try:
        await torrent_service.get_torrent(download_request.torrent_hash)
    except KeyError:
        if download_request.tracker == "c411":
            torrent_url = f"https://c411.org/api?t=get&id={download_request.torrent_hash}&apikey={download_request.api_key}"
        elif download_request.tracker == "torr9" and download_request.torrent_id:
            torrent_url = f"https://api.torr9.net/api/v1/rss/torrents/{download_request.torrent_id}/download?passkey={download_request.api_key}"
        else:
            raise HTTPException(status_code=400, detail="Invalid tracker")

        available_size = (
            request.state.user.transmission_data.size * 1024 * 1024 * 1024
            - await file_service.get_folder_size()
        )

        try:
            await torrent_service.add_torrent(
                torrent=torrent_url, max_size=available_size
            )

        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    return Response(status_code=200)
