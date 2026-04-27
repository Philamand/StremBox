from pydantic import BaseModel


class FileData(BaseModel):
    name: str
    is_dir: bool
    size: int | None = None
