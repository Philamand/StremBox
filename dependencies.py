import asyncpg
from fastapi import Depends

from db.database import get_db_conn
from services.users import UserService


async def get_user_service(
    conn: asyncpg.Connection = Depends(get_db_conn),
) -> UserService:
    """Return a UserService instance with the given database connection."""
    return UserService(conn)
