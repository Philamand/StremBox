from typing import Annotated

from fastapi import Depends, HTTPException, Path, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from users.services import UserService

security = HTTPBearer()


async def check_user_key(
    request: Request,
    user_service: Annotated[UserService, Depends()],
    user_key: str = Path(..., description="Per-user key embedded in the URL"),
) -> None:
    """Checks the user key and raises an HTTPException if it is invalid."""

    user = await user_service.get_user(api_key=user_key)

    if not user:
        raise HTTPException(status_code=401, detail="Invalid user key")

    request.state.user = user


async def validate_bearer_token(
    request: Request,
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(security)],
    user_service: Annotated[UserService, Depends()],
) -> None:
    """
    Validate the bearer token from the request.

    Args:
        credentials: The HTTP authorization credentials from the request header

    Returns:
        The valid bearer token

    Raises:
        HTTPException: If the token is invalid or missing
    """
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Jeton d'authentification manquant",
        )

    if credentials.scheme.lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Schéma d'authentification invalide. Attendu 'Bearer'",
        )

    user = await user_service.get_user(api_key=credentials.credentials)

    if not user:
        raise HTTPException(status_code=401, detail="Invalid user key")

    request.state.user = user
