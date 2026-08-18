from pydantic import BaseModel


class StremioStreamData(BaseModel):
    """Represents a stream returned by Stremio."""

    title: str
    url: str | None = None
    externalUrl: str | None = None
    filename: str
    videoSize: int


class StremioStreamsResponse(BaseModel):
    """Represents the response from Stremio containing a list of streams."""

    streams: list[StremioStreamData]
