# This file is AI-generated
import uuid

import asyncpg
import pytest

from schemas.users import UserCreateData, UserData
from services.users import UserService

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_create_data(
    librebox_url: str = "https://librebox.example.com",
    librebox_token: str = "token-abc",
    *,
    c411_key: str | None = "c411-key-123",
    torr9_key: str | None = "torr9-key-456",
    lacale_key: str | None = "lacale-key-789",
) -> UserCreateData:
    """Build a UserCreateData with sensible defaults so tests stay concise."""
    return UserCreateData(
        librebox_url=librebox_url,
        librebox_token=librebox_token,
        c411_key=c411_key,
        torr9_key=torr9_key,
        lacale_key=lacale_key,
    )


# ---------------------------------------------------------------------------
# create_user
# ---------------------------------------------------------------------------


async def test_create_user_returns_uuid_string(conn: asyncpg.Connection) -> None:
    """create_user should return the new user's ID as a string."""
    svc = UserService(conn)
    user_id = await svc.create_user(_make_create_data())

    # Must be a valid UUID (asyncpg returns a UUID object; str() for safety).
    uuid.UUID(str(user_id))


async def test_create_user_persists_all_fields(conn: asyncpg.Connection) -> None:
    """Every field supplied at creation must be persisted correctly."""
    svc = UserService(conn)
    data = _make_create_data(
        librebox_url="https://box.org",
        librebox_token="secret",
        c411_key="c411-x",
        torr9_key="torr9-y",
        lacale_key="lacale-z",
    )
    user_id = await svc.create_user(data)

    row = await conn.fetchrow("SELECT * FROM users WHERE id = $1", user_id)
    assert row is not None
    assert row["librebox_url"] == data.librebox_url
    assert row["librebox_token"] == data.librebox_token
    assert row["c411_key"] == data.c411_key
    assert row["torr9_key"] == data.torr9_key
    assert row["lacale_key"] == data.lacale_key


async def test_create_user_optional_keys_can_be_none(conn: asyncpg.Connection) -> None:
    """None values in optional key fields should round-trip as NULL."""
    svc = UserService(conn)
    data = _make_create_data(c411_key=None, torr9_key=None, lacale_key=None)
    user_id = await svc.create_user(data)

    row = await conn.fetchrow("SELECT * FROM users WHERE id = $1", user_id)
    assert row is not None
    assert row["c411_key"] is None
    assert row["torr9_key"] is None
    assert row["lacale_key"] is None


async def test_create_user_different_users_get_different_ids(
    conn: asyncpg.Connection,
) -> None:
    """Two users created independently must receive distinct IDs."""
    svc = UserService(conn)
    id_a = await svc.create_user(_make_create_data())
    id_b = await svc.create_user(_make_create_data(librebox_url="https://other.box"))
    assert id_a != id_b


# ---------------------------------------------------------------------------
# get_user
# ---------------------------------------------------------------------------


async def test_get_user_returns_user_data(conn: asyncpg.Connection) -> None:
    """get_user should return a UserData matching the created row."""
    svc = UserService(conn)
    created_id = await svc.create_user(
        _make_create_data(
            librebox_url="https://get.me",
            librebox_token="tok",
            c411_key="ck",
            torr9_key="tk",
            lacale_key="lk",
        )
    )

    user = await svc.get_user(created_id)

    assert isinstance(user, UserData)
    assert str(user.id) == str(created_id)
    assert user.librebox_url == "https://get.me"
    assert user.librebox_token == "tok"
    assert user.c411_key == "ck"
    assert user.torr9_key == "tk"
    assert user.lacale_key == "lk"


async def test_get_user_nonexistent_raises_valueerror(conn: asyncpg.Connection) -> None:
    """Querying a non-existent user ID must raise ValueError."""
    svc = UserService(conn)
    fake_id = "00000000-0000-0000-0000-000000000000"

    with pytest.raises(ValueError, match="User not found"):
        await svc.get_user(fake_id)
