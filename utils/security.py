from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from config import BEARER_TOKEN

security = HTTPBearer()


async def validate_bearer_token(
    credentials: HTTPAuthorizationCredentials = Depends(security),
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

    if credentials.credentials != BEARER_TOKEN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Jeton d'authentification invalide",
        )
