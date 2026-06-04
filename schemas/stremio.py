from typing import Optional

from pydantic import BaseModel


class StremioStreamData(BaseModel):
    """Represents a stream returned by Stremio."""

    title: str
    url: Optional[str] = None
    externalUrl: Optional[str] = None
    filename: str
    videoSize: int


class StremioStreamsResponse(BaseModel):
    """Represents the response from Stremio containing a list of streams."""

    streams: list[StremioStreamData]
