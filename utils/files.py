import shutil


def zip_directory(path: str) -> None:
    shutil.make_archive(path, "zip", path)
