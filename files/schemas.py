from pydantic import BaseModel


class FileData(BaseModel):
    name: str
    is_dir: bool
    is_archive: bool
    size: int | None = None
    last_modified: int


class ZipDirectory(BaseModel):
    id: int
    datetime: int
    done: bool
    path: str
