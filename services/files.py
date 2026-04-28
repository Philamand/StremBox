import os as _pyos

from aiofiles import os

from config import BASE_DIR
from schemas.files import FileData

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
        Return the list of entries in the configured directory.

        Results are sorted with directories first, then files; within each group they are
        sorted by name (case-insensitive).
        """
        path = self.get_path(folder)

        try:
            names = await os.listdir(path)
        except (FileNotFoundError, PermissionError):
            return []

        results: list[FileData] = []

        for name in names:
            full_path = _pyos.path.join(path, name)
            try:
                is_dir = await os.path.isdir(full_path)
                size = await os.path.getsize(full_path) if not is_dir else None
                last_modified = await os.path.getatime(full_path)
            except (FileNotFoundError, PermissionError):
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
