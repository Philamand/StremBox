import asyncpg
from fastapi import Depends, HTTPException, Path

from db.database import get_db_conn
from schemas.users import UserData
from services.users import UserService


async def get_user_service(
    conn: asyncpg.Connection = Depends(get_db_conn),
) -> UserService:
    """Return a UserService instance with the given database connection."""
    return UserService(conn)


async def get_user_key(
    user_key: str = Path(..., description="Per-user key embedded in the URL"),
    user_service: UserService = Depends(get_user_service),
) -> UserData:
    """
    Extracts the ``user_key`` path parameter and makes the corresponding user object available as a dependency.

    Returns:
        UserData: The user data corresponding to the provided user key.
    """

    try:
        user = await user_service.get_user(user_key)
    except asyncpg.exceptions.DataError:
        raise HTTPException(status_code=401, detail="Invalid user key")

    if not user:
        raise HTTPException(status_code=401, detail="Invalid user key")

    return user
