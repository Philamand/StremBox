from fastapi import APIRouter

from constants import MANIFEST

router = APIRouter()


@router.get("/manifest.json")
async def get_manifest():
    return MANIFEST
