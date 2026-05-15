"""
Unit tests for the UserService class.

This file was AI-generated.
"""

import sqlite3
import tempfile
from pathlib import Path
from unittest.mock import AsyncMock

import pytest

from services.users import UserService
from utils.database import AsyncDatabase

# Path to the schema file
SCHEMA_PATH = Path(__file__).parent.parent / "db" / "schema.sql"


@pytest.fixture
def temp_db():
    """Create a temporary database for testing using schema.sql."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp:
        db_path = tmp.name

    # Read and execute schema
    schema_content = SCHEMA_PATH.read_text()

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Execute schema file
    cursor.executescript(schema_content)
    conn.commit()
    conn.close()

    yield db_path

    # Cleanup
    Path(db_path).unlink(missing_ok=True)


@pytest.fixture
def mock_db():
    """Create a mock AsyncDatabase."""
    return AsyncMock(spec=AsyncDatabase)


@pytest.fixture
def user_service_with_mock(mock_db):
    """Create a UserService with a mocked database."""
    service = UserService(db=mock_db)
    return service


class TestGetUser:
    """Tests for UserService.get_user method."""

    @pytest.mark.asyncio
    async def test_get_user_by_id_with_transmission(
        self, user_service_with_mock, mock_db
    ):
        """Test getting a user by ID with transmission data."""
        # Setup mock return value
        user_row = {
            "id": "user123",
            "created_at": "2024-01-15T10:30:00",
            "api_key": "api-key-123",
            "port": 6969,
            "download_folder": "/downloads",
            "size": 1024,
        }
        mock_db.fetch_one.return_value = user_row

        # Execute
        result = await user_service_with_mock.get_user(id="user123")

        # Assert
        assert result is not None
        assert result.id == "user123"
        assert result.api_key == "api-key-123"
        assert result.transmission_data is not None
        assert result.transmission_data.port == 6969
        assert result.transmission_data.download_folder == "/downloads"
        assert result.transmission_data.size == 1024

        # Verify the correct query was used
        mock_db.fetch_one.assert_called_once()
        call_args = mock_db.fetch_one.call_args
        assert "WHERE users.id = ?" in call_args[0][0]

    @pytest.mark.asyncio
    async def test_get_user_by_api_key(self, user_service_with_mock, mock_db):
        """Test getting a user by API key."""
        user_row = {
            "id": "user456",
            "created_at": "2024-01-20T14:45:00",
            "api_key": "api-key-456",
            "port": 7070,
            "download_folder": "/downloads",
            "size": 2048,
        }
        mock_db.fetch_one.return_value = user_row

        # Execute
        result = await user_service_with_mock.get_user(api_key="api-key-456")

        # Assert
        assert result is not None
        assert result.id == "user456"
        assert result.api_key == "api-key-456"

        # Verify the correct query was used
        call_args = mock_db.fetch_one.call_args
        assert "WHERE users.api_key = ?" in call_args[0][0]

    @pytest.mark.asyncio
    async def test_get_user_without_transmission_data(
        self, user_service_with_mock, mock_db
    ):
        """Test getting a user without transmission data."""
        user_row = {
            "id": "user789",
            "created_at": "2024-02-01T08:00:00",
            "api_key": "api-key-789",
            "port": None,
            "download_folder": None,
            "size": None,
        }
        mock_db.fetch_one.return_value = user_row

        # Execute
        result = await user_service_with_mock.get_user(id="user789")

        # Assert
        assert result is not None
        assert result.id == "user789"
        assert result.transmission_data is None

    @pytest.mark.asyncio
    async def test_get_user_not_found_by_id(self, user_service_with_mock, mock_db):
        """Test getting a non-existent user by ID."""
        mock_db.fetch_one.return_value = None

        # Execute
        result = await user_service_with_mock.get_user(id="nonexistent")

        # Assert
        assert result is None

    @pytest.mark.asyncio
    async def test_get_user_not_found_by_api_key(self, user_service_with_mock, mock_db):
        """Test getting a non-existent user by API key."""
        mock_db.fetch_one.return_value = None

        # Execute
        result = await user_service_with_mock.get_user(api_key="nonexistent-key")

        # Assert
        assert result is None

    @pytest.mark.asyncio
    async def test_get_user_with_neither_id_nor_api_key(
        self, user_service_with_mock, mock_db
    ):
        """Test get_user with neither ID nor API key returns None."""
        # Execute
        result = await user_service_with_mock.get_user()

        # Assert
        assert result is None
        # Database should not be queried
        mock_db.fetch_one.assert_not_called()

    @pytest.mark.asyncio
    async def test_get_user_with_both_id_and_api_key_prioritizes_api_key(
        self, user_service_with_mock, mock_db
    ):
        """Test that API key takes priority when both ID and API key are provided."""
        user_row = {
            "id": "user123",
            "created_at": "2024-01-15T10:30:00",
            "api_key": "api-key-123",
            "port": None,
            "download_folder": None,
            "size": None,
        }
        mock_db.fetch_one.return_value = user_row

        # Execute
        await user_service_with_mock.get_user(id="user123", api_key="api-key-123")

        # Assert
        # Should have queried with API key
        call_args = mock_db.fetch_one.call_args
        assert "WHERE users.api_key = ?" in call_args[0][0]


class TestGetUserList:
    """Tests for UserService.get_user_list method."""

    @pytest.mark.asyncio
    async def test_get_user_list_with_multiple_users(
        self, user_service_with_mock, mock_db
    ):
        """Test getting a list of multiple users."""
        users_rows = [
            {
                "id": "user1",
                "created_at": "2024-01-01T00:00:00",
                "api_key": "api-1",
                "port": 6969,
                "download_folder": "/dl1",
                "size": 1024,
            },
            {
                "id": "user2",
                "created_at": "2024-01-02T00:00:00",
                "api_key": "api-2",
                "port": None,
                "download_folder": None,
                "size": None,
            },
            {
                "id": "user3",
                "created_at": "2024-01-03T00:00:00",
                "api_key": "api-3",
                "port": 7070,
                "download_folder": "/dl3",
                "size": 2048,
            },
        ]
        mock_db.fetch_all.return_value = users_rows

        # Execute
        result = await user_service_with_mock.get_user_list()

        # Assert
        assert len(result) == 3
        assert result[0].id == "user1"
        assert result[0].transmission_data.port == 6969
        assert result[1].id == "user2"
        assert result[1].transmission_data is None
        assert result[2].id == "user3"
        assert result[2].transmission_data.port == 7070

    @pytest.mark.asyncio
    async def test_get_user_list_empty(self, user_service_with_mock, mock_db):
        """Test getting an empty user list."""
        mock_db.fetch_all.return_value = []

        # Execute
        result = await user_service_with_mock.get_user_list()

        # Assert
        assert result == []

    @pytest.mark.asyncio
    async def test_get_user_list_all_without_transmission(
        self, user_service_with_mock, mock_db
    ):
        """Test getting a user list where all users have no transmission data."""
        users_rows = [
            {
                "id": "user1",
                "created_at": "2024-01-01T00:00:00",
                "api_key": "api-1",
                "port": None,
                "download_folder": None,
                "size": None,
            },
            {
                "id": "user2",
                "created_at": "2024-01-02T00:00:00",
                "api_key": "api-2",
                "port": None,
                "download_folder": None,
                "size": None,
            },
        ]
        mock_db.fetch_all.return_value = users_rows

        # Execute
        result = await user_service_with_mock.get_user_list()

        # Assert
        assert len(result) == 2
        assert all(user.transmission_data is None for user in result)


class TestDeleteUser:
    """Tests for UserService.delete_user method."""

    @pytest.mark.asyncio
    async def test_delete_user(self, user_service_with_mock, mock_db):
        """Test deleting a user."""
        # Execute
        await user_service_with_mock.delete_user("user123")

        # Assert
        mock_db.commit_execute.assert_called_once()
        call_args = mock_db.commit_execute.call_args
        assert "DELETE FROM users WHERE id = ?" in call_args[0][0]
        assert call_args[0][1] == ("user123",)

    @pytest.mark.asyncio
    async def test_delete_user_with_special_characters(
        self, user_service_with_mock, mock_db
    ):
        """Test deleting a user with special characters in ID."""
        user_id = "user-123-abc"

        # Execute
        await user_service_with_mock.delete_user(user_id)

        # Assert
        call_args = mock_db.commit_execute.call_args
        assert call_args[0][1] == (user_id,)


class TestCreateUser:
    """Tests for UserService.create_user method."""

    @pytest.mark.asyncio
    async def test_create_user(self, user_service_with_mock, mock_db):
        """Test creating a new user."""
        # Execute
        await user_service_with_mock.create_user("user123", 1)

        # Assert
        mock_db.commit_execute.assert_called_once()
        call_args = mock_db.commit_execute.call_args
        query = call_args[0][0]
        params = call_args[0][1]

        assert "INSERT INTO users" in query
        assert params[0] == "user123"
        assert params[2] == 1
        # Verify that a UUID was generated for the API key
        assert isinstance(params[1], str)
        assert len(params[1]) == 36  # UUID4 string length

    @pytest.mark.asyncio
    async def test_create_user_with_different_transmission_ids(
        self, user_service_with_mock, mock_db
    ):
        """Test creating users with different transmission IDs."""
        # Execute first user
        await user_service_with_mock.create_user("user1", 1)
        first_call_params = mock_db.commit_execute.call_args[0][1]

        # Reset mock
        mock_db.reset_mock()

        # Execute second user
        await user_service_with_mock.create_user("user2", 2)
        second_call_params = mock_db.commit_execute.call_args[0][1]

        # Assert
        assert first_call_params[0] == "user1"
        assert first_call_params[2] == 1
        assert second_call_params[0] == "user2"
        assert second_call_params[2] == 2


class TestUserServiceIntegration:
    """Integration tests using a real temporary database."""

    @pytest.mark.asyncio
    async def test_full_user_workflow(self, temp_db):
        """Test a complete workflow: create, retrieve, and delete a user."""
        db = AsyncDatabase(temp_db)

        # Manually insert test data to avoid UUID generation issues
        async with db.connection() as conn:
            await conn.execute(
                """INSERT INTO users (id, api_key, transmission_id)
                   VALUES (?, ?, ?)""",
                ("test_user", "test_api_key_123", None),
            )
            await conn.commit()

        # Create service with real database
        service = UserService(db=db)

        # Test get_user by ID
        user = await service.get_user(id="test_user")
        assert user is not None
        assert user.id == "test_user"
        assert user.api_key == "test_api_key_123"
        assert user.transmission_data is None

        # Test get_user by API key
        user = await service.get_user(api_key="test_api_key_123")
        assert user is not None
        assert user.id == "test_user"

        # Test delete_user
        await service.delete_user("test_user")

        # Verify deletion
        user = await service.get_user(id="test_user")
        assert user is None

    @pytest.mark.asyncio
    async def test_user_list_with_transmission_data(self, temp_db):
        """Test retrieving a list of users with transmission data."""
        db = AsyncDatabase(temp_db)

        # Insert transmission data
        async with db.connection() as conn:
            await conn.execute(
                """INSERT INTO transmission (id, port, download_folder, size)
                   VALUES (?, ?, ?, ?)""",
                (1, 6969, "/downloads", 1024),
            )
            await conn.execute(
                """INSERT INTO transmission (id, port, download_folder, size)
                   VALUES (?, ?, ?, ?)""",
                (2, 7070, "/files", 2048),
            )
            # Insert users
            await conn.execute(
                """INSERT INTO users (id, api_key, transmission_id)
                   VALUES (?, ?, ?)""",
                ("user1", "api-1", 1),
            )
            await conn.execute(
                """INSERT INTO users (id, api_key, transmission_id)
                   VALUES (?, ?, ?)""",
                ("user2", "api-2", 2),
            )
            await conn.commit()

        service = UserService(db=db)

        # Test get_user_list
        users = await service.get_user_list()

        assert len(users) == 2
        assert users[0].id == "user1"
        assert users[0].transmission_data is not None
        assert users[0].transmission_data.port == 6969
        assert users[1].id == "user2"
        assert users[1].transmission_data is not None
        assert users[1].transmission_data.port == 7070
