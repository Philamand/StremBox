import asyncio
import shutil
from typing import Annotated

from fastapi import Depends

from files.services import ZipDirectoryService


async def zip_directory(
    path: str, zip_id: int, zip_service: Annotated[ZipDirectoryService, Depends()]
) -> None:
    await asyncio.to_thread(shutil.make_archive, path, "zip", path)
    await zip_service.update_zip(zip_id)
