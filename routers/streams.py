from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import FileResponse

from services.files import FileManager
from utils.security import check_user_key

router = APIRouter(prefix="/streams", dependencies=[Depends(check_user_key)])


@router.get("/{user_key}")
async def get_stream(
    request: Request,
    file_manager: Annotated[FileManager, Depends()],
    file_path: str,
) -> FileResponse:
    """Return a stream of the file at the given path."""
    path = file_manager.get_path(file_path)

    if not await file_manager.exists(path):
        raise HTTPException(status_code=404, detail="File not found")

    return FileResponse(path)
