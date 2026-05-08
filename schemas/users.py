from datetime import datetime

from pydantic import BaseModel


class User(BaseModel):
    id: str
    created_at: datetime
    transmission_host: str | None
    transmission_port: int | None
