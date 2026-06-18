from typing import Annotated

import aiohttp
from fastapi import Depends, Path, Request
from fastapi.exceptions import HTTPException

from core.config import settings
from core.database import AsyncDatabaseDep
from core.htmx import is_htmx_request
from users.schemas import UserData
from users.services import UserService


def get_user_service(db: AsyncDatabaseDep) -> UserService:
    """Factory dependency that creates a UserService."""
    return UserService(db=db)


UserServiceDep = Annotated[UserService, Depends(get_user_service)]

UserKeyDep = Annotated[str, Path(description="Per-user key embedded in the URL")]


async def get_user(request: Request, user_service: UserServiceDep) -> UserData | None:
    credentials = request.cookies.get("hanko")
    if not credentials:
        return
    async with aiohttp.ClientSession() as session:
        async with session.post(
            settings.hanko_url + "/sessions/validate",
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


GetUserDep = Annotated[UserData | None, Depends(get_user)]


async def require_auth(request: Request, user: GetUserDep) -> UserData:
    """Dependency that requires authentication and raises NotAuthenticatedException if not authenticated."""
    if not user:
        if is_htmx_request(request):
            raise HTTPException(status_code=401)
        raise NotAuthenticatedException()
    return user


RequireAuthDep = Annotated[UserData, Depends(require_auth)]


class NotAuthenticatedException(Exception):
    pass
