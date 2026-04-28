import os as _pyos

from aiofiles import os

from config import BASE_DIR
from schemas.files import FileData


class FileManager:
    def get_path(self, folder: str | None = None) -> str:
        """Return the path to the given folder, or the base directory if no folder is given."""
        return _pyos.path.join(BASE_DIR, folder) if folder else BASE_DIR

    async def is_dir(self, path) -> bool:
        """Return True if the path is a directory."""
        return await os.path.isdir(path)

    async def exists(self, path) -> bool:
        """Return True if the path exists."""
        return await os.path.exists(path)

    async def list_files(self, folder: str | None = None) -> list[FileData]:
        """
        Return the list of entries in the configured Torrents directory.
        """
        path = self.get_path(folder)
        names = await os.listdir(path)
        results: list[FileData] = []

        for name in names:
            full_path = _pyos.path.join(path, name)
            try:
                is_dir = await os.path.isdir(full_path)
                size = await os.path.getsize(full_path) if not is_dir else None
                last_modified = await os.path.getatime(full_path)
            except (FileNotFoundError, PermissionError):
                continue

            results.append(
                FileData(
                    name=name,
                    is_dir=is_dir,
                    size=size,
                    last_modified=int(last_modified),
                )
            )

        return results
