import os as _pyos
from typing import Annotated

from aiofiles import os
from fastapi import Depends, Request

from core.database import AsyncDatabase
from files.schemas import FileData, ZipDirectory

ARCHIVE_EXTENSIONS = (
    ".zip",
    ".rar",
    ".tar",
    ".tar.gz",
    ".tgz",
    ".tar.bz2",
    ".tbz",
    ".7z",
    ".gz",
    ".bz2",
    ".xz",
)


class FileManager:
    def __init__(self, request: Request):
        self.base_dir = request.state.user.transmission_data.download_folder

    def get_path(self, folder: str | None = None) -> str:
        """Return the path to the given folder, or the base directory if no folder is given."""
        return _pyos.path.join(self.base_dir, folder) if folder else self.base_dir

    async def is_dir(self, path) -> bool:
        """Return True if the path is a directory."""
        return await os.path.isdir(path)

    async def exists(self, path) -> bool:
        """Return True if the path exists."""
        return await os.path.exists(path)

    async def list_files(self, folder: str | None = None) -> list[FileData]:
        """
        Return the list of entries in the configured directory.

        Results are sorted with directories first, then files; within each group they are
        sorted by name (case-insensitive).
        """
        path = self.get_path(folder)

        try:
            names = await os.listdir(path)
        except FileNotFoundError, PermissionError:
            return []

        results: list[FileData] = []

        for name in names:
            full_path = _pyos.path.join(path, name)
            try:
                is_dir = await os.path.isdir(full_path)
                size = await os.path.getsize(full_path) if not is_dir else None
                last_modified = await os.path.getatime(full_path)
            except FileNotFoundError, PermissionError:
                continue

            is_archive = False
            if not is_dir:
                lower_name = name.lower()
                is_archive = any(lower_name.endswith(ext) for ext in ARCHIVE_EXTENSIONS)

            results.append(
                FileData(
                    name=name,
                    is_dir=is_dir,
                    is_archive=is_archive,
                    size=size,
                    last_modified=int(last_modified),
                )
            )

        results_sorted = sorted(results, key=lambda f: (not f.is_dir, f.name.lower()))
        return results_sorted

    async def remove_file(self, file_path: str) -> None:
        """Remove the file at the given path."""
        full_path = self.get_path(file_path)
        is_file = await os.path.isfile(full_path)
        if is_file:
            await os.remove(full_path)
            return
        is_dir = await os.path.isdir(full_path)
        if is_dir:
            await os.rmdir(full_path)
        else:
            raise FileNotFoundError(f"File not found: {full_path}")

    async def get_folder_size(self, folder: str | None = None) -> int:
        """Return the total size of the folder in bytes, recursively including all files."""
        path = self.get_path(folder)

        try:
            if not await os.path.isdir(path):
                return 0
        except FileNotFoundError, PermissionError:
            return 0

        total_size = 0

        try:
            for root, dirs, files in _pyos.walk(path):
                for file in files:
                    file_path = _pyos.path.join(root, file)
                    try:
                        total_size += await os.path.getsize(file_path)
                    except FileNotFoundError, PermissionError:
                        continue
        except FileNotFoundError, PermissionError:
            pass

        return total_size

    async def get_size(self, file_path: str) -> int:
        """Return the size of the file in bytes."""
        return await os.path.getsize(file_path)


class ZipDirectoryService:
    """Service for managing zip directory entries."""

    def __init__(self, db: Annotated[AsyncDatabase, Depends()]):
        self.db = db

    async def create_zip(self, path: str) -> int:
        """Create a zip file entry and return the ID."""
        row = await self.db.commit_fetch_one(
            "INSERT INTO zip_directory (path) VALUES (?) RETURNING id",
            (path,),
        )
        return row["id"]

    async def get_zip(self, zip_id: int) -> ZipDirectory:
        """Return the zip file entry by ID."""
        row = await self.db.fetch_one(
            "SELECT * FROM zip_directory WHERE id = ?",
            (zip_id,),
        )
        return ZipDirectory(**row)

    async def update_zip(self, zip_id: int):
        """Update a zip file entry."""
        await self.db.commit_execute(
            "UPDATE zip_directory SET done = true WHERE id = ?", (zip_id,)
        )

    async def delete_zip(self, zip_id: int):
        """Delete a zip file entry."""
        await self.db.commit_execute(
            "DELETE FROM zip_directory WHERE id = ?", (zip_id,)
        )
