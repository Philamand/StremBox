from pydantic import BaseModel


class TraktPlexIds(BaseModel):
    guid: str | None = None
    slug: str | None = None


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


class TraktShowIds(BaseModel):
    imdb: str | None = None
    plex: TraktPlexIds | None = None
    slug: str | None = None
    tmdb: int | None = None
    tvdb: int | None = None
    trakt: int | None = None


class TraktShow(BaseModel):
    ids: TraktShowIds
    title: str
    year: int | None = None
    aired_episodes: int | None = None


class TraktHistoryEntry(BaseModel):
    id: int
    watched_at: str
    action: str
    type: str
    episode: TraktEpisode
    show: TraktShow


class TraktMovieIds(BaseModel):
    imdb: str | None = None
    plex: TraktPlexIds | None = None
    slug: str | None = None
    tmdb: int | None = None
    trakt: int | None = None


class TraktMovie(BaseModel):
    ids: TraktMovieIds
    title: str
    year: int | None = None


class TraktWatchlistMovie(BaseModel):
    type: str
    movie: TraktMovie
    rank: int
    id: int
    listed_at: str
    notes: str | None = None
    my_rating: int | None = None


class TraktWatchlistShow(BaseModel):
    type: str
    show: TraktShow
    rank: int
    id: int
    listed_at: str
    notes: str | None = None
    my_rating: int | None = None
