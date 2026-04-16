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
    db_conn: asyncpg.Connection = Depends(get_db_conn),
    user_key: str = Path(..., description="Per-user key embedded in the URL"),
) -> UserData:
    """
    Extracts the ``user_key`` path parameter and makes the corresponding user object available as a dependency.

    Returns:
        UserData: The user data corresponding to the provided user key.
    """

    try:
        row = await db_conn.fetchrow(
            "SELECT * FROM users WHERE id = $1",
            user_key,
        )
    except asyncpg.exceptions.DataError:
        raise HTTPException(status_code=401, detail="Invalid user key")

    if not row:
        raise HTTPException(status_code=401, detail="Invalid user key")

    user = UserData(**row)

    return user
