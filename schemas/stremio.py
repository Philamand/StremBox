from pydantic import BaseModel


class StremioTorrentData(BaseModel):
    """Represents a torrent returned by Stremio's streams."""

    title: str
    infoHash: str
    sources: list[str]
    filename: str
    videoSize: int


class StremioStreamData(BaseModel):
    """Represents a stream returned by Stremio."""

    title: str
    url: str
    filename: str
    videoSize: int


class StremioStreamsResponse(BaseModel):
    """Represents the response from Stremio containing a list of streams."""

    streams: list[StremioStreamData | StremioTorrentData]
