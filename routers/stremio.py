from fastapi import APIRouter, Depends, HTTPException, status

from constants import MANIFEST
from dependencies import get_user_key
from schemas.stremio import StremioStreamsResponse
from schemas.users import UserData
from services.stremio import C411Service, StremioOrchestrationService, Torr9Service

router = APIRouter()


@router.get("/{user_key}/manifest.json")
async def get_manifest(user: UserData = Depends(get_user_key)):
    """Return the manifest.json file."""
    return MANIFEST


@router.get("/{user_key}/stream/{type}/{id}.json")
async def get_torrent_streams(
    type: str,
    id: str,
    user: UserData = Depends(get_user_key),
) -> StremioStreamsResponse:
    """
    Return Stremio-compatible stream entries for a movie or series.

    Path parameters:
    - type: ``"movie"`` or ``"series"`` (must be declared in the manifest).
    - id: IMDb id for movies (e.g. ``"tt1234567"``); for series the combined
      form ``"{imdbid}:{season}:{episode}"`` (e.g. ``"tt1234567:1:2"``).

    Results are cached in Redis for one hour. An empty stream list is not
    cached so transient failures do not poison the cache.
    """
    if type not in MANIFEST["types"]:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)

    if user.c411_key:
        c411_service = C411Service(user.c411_key)
    else:
        c411_service = None

    if user.torr9_key:
        torr9_service = Torr9Service(user.torr9_key)
    else:
        torr9_service = None

    stremio_service = StremioOrchestrationService(
        user.streamer_url,
        user.streamer_token,
        c411_service=c411_service,
        torr9_service=torr9_service,
    )

    response = await stremio_service.get_streams(type=type, id=id, user=user)

    return response
