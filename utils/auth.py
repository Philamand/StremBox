from typing import Annotated

import aiohttp
from fastapi import Depends, Request
from fastapi.exceptions import HTTPException

from config import HANKO_URL
from services.users import UserService
from utils.htmx import is_htmx_request


class NotAuthenticatedException(Exception):
    pass


async def get_user(request: Request, user_service: Annotated[UserService, Depends()]):
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

            user = await user_service.get_user(id=validation_data.get("user_id"))

            if not user:
                raise HTTPException(status_code=403)

            request.state.user = user

            return user


async def require_auth(request: Request, user=Depends(get_user)):
    """Dependency that requires authentication and raises NotAuthenticatedException if not authenticated."""
    if not user:
        if is_htmx_request(request):
            raise HTTPException(status_code=401)
        raise NotAuthenticatedException()
