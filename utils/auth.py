import aiohttp
from fastapi.exceptions import HTTPException

from config import HANKO_ADMIN, HANKO_URL
from fastapi import Request


async def get_user(request: Request):
    credentials = request.cookies.get("hanko")
    if not credentials:
        return
    async with aiohttp.ClientSession() as session:
        async with session.post(
            HANKO_URL + "/sessions/validate",
            json={"session_token": credentials},
        ) as response:
            if response.status != 200:
                raise HTTPException(status_code=response.status)

            validation_data = await response.json()

            if not validation_data.get("is_valid", False):
                return

            if validation_data.get("user_id") != HANKO_ADMIN:
                raise HTTPException(status_code=403)

            return validation_data
