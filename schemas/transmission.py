from pydantic import BaseModel


class TransmissionData(BaseModel):
    id: int
    port: int
    download_folder: str
    size: int
