from typing import Optional

from pydantic import BaseModel


class DownloadRequest(BaseModel):
    torrent_hash: str
    tracker: str
    api_key: str
    torrent_id: Optional[int] = None
