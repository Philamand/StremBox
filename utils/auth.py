import aiohttp
from fastapi import Request
from fastapi.exceptions import HTTPException

from config import HANKO_URL


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
            return validation_data
