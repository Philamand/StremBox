from fastapi import APIRouter, Depends

from constants import MANIFEST
from dependencies import get_user_key
from schemas.users import UserData

router = APIRouter()


@router.get("/{user_key}/manifest.json")
async def get_manifest(user: UserData = Depends(get_user_key)):
    """Return the manifest.json file."""
    return MANIFEST
