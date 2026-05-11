from datetime import datetime

from pydantic import BaseModel


class TransmissionData(BaseModel):
    port: int
    download_folder: str
    size: int


class UserData(BaseModel):
    id: str
    created_at: datetime
    transmission_data: TransmissionData | None
