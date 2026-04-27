import os as _pyos

from aiofiles import os

from config import BASE_DIR
from schemas.files import FileData


class FileManager:
    async def list_files(self, folder: str | None = None) -> list[FileData]:
        """
        Return the list of entries in the configured Torrents directory.
        """
        path = _pyos.path.join(BASE_DIR, folder) if folder else BASE_DIR
        names = await os.listdir(path)
        results: list[FileData] = []

        for name in names:
            full_path = _pyos.path.join(path, name)
            try:
                is_dir = await os.path.isdir(full_path)
                size = await os.path.getsize(full_path) if not is_dir else None
            except (FileNotFoundError, PermissionError):
                continue

            results.append(FileData(name=name, is_dir=is_dir, size=size))

        return results
