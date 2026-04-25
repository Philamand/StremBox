from pydantic import BaseModel


class Torrent(BaseModel):
    name: str
    dlspeed: int
    upspeed: int
    hash: str
    num_seeds: int
    num_leechs: int
