from pydantic import BaseModel


class TraktPlexIds(BaseModel):
    guid: str | None = None


class TraktSeasonIds(BaseModel):
    plex: TraktPlexIds | None = None
    tmdb: int | None = None
    tvdb: int | None = None
    trakt: int | None = None


class TraktEpisodeIds(BaseModel):
    imdb: str | None = None
    plex: TraktPlexIds | None = None
    tmdb: int | None = None
    tvdb: int | None = None
    trakt: int | None = None


class TraktEpisode(BaseModel):
    ids: TraktEpisodeIds
    title: str | None = None
    number: int
    season: int


class TraktSeason(BaseModel):
    ids: TraktSeasonIds
    number: int
    episodes: list[TraktEpisode]
