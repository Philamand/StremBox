import asyncio
import os
import shutil
import tarfile
import zipfile

from files.services import UnzipService, ZipDirectoryService


async def zip_directory(
    path: str, zip_id: int, zip_service: ZipDirectoryService
) -> None:
    """
    Zip directory in background task.
    """
    await asyncio.to_thread(shutil.make_archive, path, "zip", path)
    await zip_service.update_zip(zip_id)


async def unzip_archive(
    archive_path: str,
    destination: str,
    unzip_id: int,
    unzip_service: UnzipService,
) -> None:
    """
    Extract archive in background task.
    Supports .zip, .tar.gz, .tar.bz2, .tgz, .tbz
    """
    archive_path = os.path.abspath(archive_path)
    destination = os.path.abspath(destination)

    os.makedirs(destination, exist_ok=True)

    lower_path = archive_path.lower()

    if lower_path.endswith(".zip"):
        with zipfile.ZipFile(archive_path, "r") as zip_ref:
            for file_info in zip_ref.infolist():
                extracted_path = os.path.join(destination, file_info.filename)
                if not extracted_path.startswith(destination):
                    raise ValueError(
                        f"Path traversal detected in zip: {file_info.filename}"
                    )
            zip_ref.extractall(destination)

    elif lower_path.endswith((".tar.gz", ".tgz")):
        with tarfile.open(archive_path, "r:gz") as tar_ref:
            for member in tar_ref.getmembers():
                extracted_path = os.path.join(destination, member.name)
                if not extracted_path.startswith(destination):
                    raise ValueError(
                        f"Path traversal detected in tar.gz: {member.name}"
                    )
            tar_ref.extractall(destination)

    elif lower_path.endswith((".tar.bz2", ".tbz")):
        with tarfile.open(archive_path, "r:bz2") as tar_ref:
            for member in tar_ref.getmembers():
                extracted_path = os.path.join(destination, member.name)
                if not extracted_path.startswith(destination):
                    raise ValueError(
                        f"Path traversal detected in tar.bz2: {member.name}"
                    )
            tar_ref.extractall(destination)

    elif lower_path.endswith(".tar"):
        with tarfile.open(archive_path, "r:") as tar_ref:
            for member in tar_ref.getmembers():
                extracted_path = os.path.join(destination, member.name)
                if not extracted_path.startswith(destination):
                    raise ValueError(f"Path traversal detected in tar: {member.name}")
            tar_ref.extractall(destination)

    else:
        raise ValueError(f"Unsupported archive format: {archive_path}")

    await unzip_service.update_extraction(unzip_id)
