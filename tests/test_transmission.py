"""
Unit tests for the TransmissionService class.

This file was AI-generated.
"""

import sqlite3
import tempfile
from pathlib import Path
from unittest.mock import AsyncMock

import pytest

from services.transmission import TransmissionService
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
def transmission_service_with_mock(mock_db):
    """Create a TransmissionService with a mocked database."""
    service = TransmissionService(db=mock_db)
    return service


class TestCreateTransmission:
    """Tests for TransmissionService.create_transmission method."""

    @pytest.mark.asyncio
    async def test_create_transmission(self, transmission_service_with_mock, mock_db):
        """Test creating a new transmission."""
        await transmission_service_with_mock.create_transmission(
            port=6969, download_folder="/downloads", size=1024
        )

        mock_db.commit_execute.assert_called_once()
        call_args = mock_db.commit_execute.call_args
        query = call_args[0][0]
        params = call_args[0][1]

        assert "INSERT INTO transmission" in query
        assert "(port, download_folder, size)" in query
        assert "VALUES (?, ?, ?)" in query
        assert params == (6969, "/downloads", 1024)

    @pytest.mark.asyncio
    async def test_create_transmission_with_different_params(
        self, transmission_service_with_mock, mock_db
    ):
        """Test creating transmissions with different parameters."""
        # First call
        await transmission_service_with_mock.create_transmission(
            port=8080, download_folder="/data", size=512
        )
        first_params = mock_db.commit_execute.call_args[0][1]

        mock_db.reset_mock()

        # Second call
        await transmission_service_with_mock.create_transmission(
            port=9090, download_folder="/media", size=2048
        )
        second_params = mock_db.commit_execute.call_args[0][1]

        assert first_params == (8080, "/data", 512)
        assert second_params == (9090, "/media", 2048)

    @pytest.mark.asyncio
    async def test_create_transmission_with_zero_size(
        self, transmission_service_with_mock, mock_db
    ):
        """Test creating a transmission with size 0."""
        await transmission_service_with_mock.create_transmission(
            port=6969, download_folder="/downloads", size=0
        )

        call_args = mock_db.commit_execute.call_args
        params = call_args[0][1]
        assert params == (6969, "/downloads", 0)


class TestGetTransmissionList:
    """Tests for TransmissionService.get_transmission_list method."""

    @pytest.mark.asyncio
    async def test_get_transmission_list_with_multiple(
        self, transmission_service_with_mock, mock_db
    ):
        """Test getting a list of multiple transmissions."""
        rows = [
            {
                "id": 1,
                "created_at": "2024-01-01T00:00:00",
                "port": 6969,
                "download_folder": "/downloads",
                "size": 1024,
            },
            {
                "id": 2,
                "created_at": "2024-01-02T00:00:00",
                "port": 7070,
                "download_folder": "/files",
                "size": 2048,
            },
            {
                "id": 3,
                "created_at": "2024-01-03T00:00:00",
                "port": 8080,
                "download_folder": "/media",
                "size": 4096,
            },
        ]
        mock_db.fetch_all.return_value = rows

        result = await transmission_service_with_mock.get_transmission_list()

        assert len(result) == 3
        assert result[0].id == 1
        assert result[0].port == 6969
        assert result[0].download_folder == "/downloads"
        assert result[0].size == 1024
        assert result[1].id == 2
        assert result[1].port == 7070
        assert result[2].id == 3
        assert result[2].port == 8080

        mock_db.fetch_all.assert_called_once()
        call_args = mock_db.fetch_all.call_args
        assert "SELECT * FROM transmission" in call_args[0][0]

    @pytest.mark.asyncio
    async def test_get_transmission_list_empty(
        self, transmission_service_with_mock, mock_db
    ):
        """Test getting an empty transmission list."""
        mock_db.fetch_all.return_value = []

        result = await transmission_service_with_mock.get_transmission_list()

        assert result == []

    @pytest.mark.asyncio
    async def test_get_transmission_list_single(
        self, transmission_service_with_mock, mock_db
    ):
        """Test getting a list with a single transmission."""
        rows = [
            {
                "id": 1,
                "created_at": "2024-01-01T00:00:00",
                "port": 6969,
                "download_folder": "/downloads",
                "size": 1024,
            },
        ]
        mock_db.fetch_all.return_value = rows

        result = await transmission_service_with_mock.get_transmission_list()

        assert len(result) == 1
        assert result[0].id == 1
        assert isinstance(result[0].port, int)
        assert isinstance(result[0].download_folder, str)
        assert isinstance(result[0].size, int)


class TestDeleteTransmission:
    """Tests for TransmissionService.delete_transmission method."""

    @pytest.mark.asyncio
    async def test_delete_transmission(self, transmission_service_with_mock, mock_db):
        """Test deleting a transmission by ID."""
        await transmission_service_with_mock.delete_transmission(1)

        mock_db.commit_execute.assert_called_once()
        call_args = mock_db.commit_execute.call_args
        query = call_args[0][0]
        params = call_args[0][1]

        assert "DELETE FROM transmission WHERE id = ?" in query
        assert params == (1,)

    @pytest.mark.asyncio
    async def test_delete_transmission_with_different_ids(
        self, transmission_service_with_mock, mock_db
    ):
        """Test deleting transmissions with different IDs."""
        await transmission_service_with_mock.delete_transmission(42)
        first_params = mock_db.commit_execute.call_args[0][1]

        mock_db.reset_mock()

        await transmission_service_with_mock.delete_transmission(99)
        second_params = mock_db.commit_execute.call_args[0][1]

        assert first_params == (42,)
        assert second_params == (99,)

    @pytest.mark.asyncio
    async def test_delete_nonexistent_transmission(
        self, transmission_service_with_mock, mock_db
    ):
        """Test deleting a non-existent transmission (should not raise an error)."""
        # Deleting a non-existent transmission should not throw
        await transmission_service_with_mock.delete_transmission(999999)

        mock_db.commit_execute.assert_called_once()
        call_args = mock_db.commit_execute.call_args
        params = call_args[0][1]
        assert params == (999999,)


class TestTransmissionServiceIntegration:
    """Integration tests using a real temporary database."""

    @pytest.mark.asyncio
    async def test_full_transmission_workflow(self, temp_db):
        """Test a complete workflow: create, list, and delete a transmission."""
        db = AsyncDatabase(temp_db)
        service = TransmissionService(db=db)

        # Create a transmission
        await service.create_transmission(
            port=6969, download_folder="/downloads", size=1024
        )

        # List and verify
        transmissions = await service.get_transmission_list()
        assert len(transmissions) == 1
        assert transmissions[0].port == 6969
        assert transmissions[0].download_folder == "/downloads"
        assert transmissions[0].size == 1024
        assert isinstance(transmissions[0].id, int)

        # Delete the transmission
        await service.delete_transmission(transmissions[0].id)

        # Verify deletion
        transmissions = await service.get_transmission_list()
        assert len(transmissions) == 0

    @pytest.mark.asyncio
    async def test_create_and_list_multiple_transmissions(self, temp_db):
        """Test creating and listing multiple transmissions."""
        db = AsyncDatabase(temp_db)
        service = TransmissionService(db=db)

        # Create multiple transmissions
        await service.create_transmission(
            port=6969, download_folder="/downloads", size=1024
        )
        await service.create_transmission(
            port=7070, download_folder="/media", size=2048
        )
        await service.create_transmission(
            port=8080, download_folder="/files", size=4096
        )

        # List and verify
        transmissions = await service.get_transmission_list()
        assert len(transmissions) == 3

        ports = {t.port for t in transmissions}
        folders = {t.download_folder for t in transmissions}
        sizes = {t.size for t in transmissions}

        assert ports == {6969, 7070, 8080}
        assert folders == {"/downloads", "/media", "/files"}
        assert sizes == {1024, 2048, 4096}

    @pytest.mark.asyncio
    async def test_delete_one_of_many_transmissions(self, temp_db):
        """Test deleting one transmission when multiple exist."""
        db = AsyncDatabase(temp_db)
        service = TransmissionService(db=db)

        # Create two transmissions
        await service.create_transmission(
            port=6969, download_folder="/downloads", size=1024
        )
        await service.create_transmission(
            port=7070, download_folder="/media", size=2048
        )

        transmissions = await service.get_transmission_list()
        assert len(transmissions) == 2

        # Delete the first one
        await service.delete_transmission(transmissions[0].id)

        # Verify only one remains
        transmissions = await service.get_transmission_list()
        assert len(transmissions) == 1
        assert transmissions[0].port == 7070

    @pytest.mark.asyncio
    async def test_create_transmission_persists_id(self, temp_db):
        """Test that created transmissions get auto-incremented IDs."""
        db = AsyncDatabase(temp_db)
        service = TransmissionService(db=db)

        await service.create_transmission(
            port=6969, download_folder="/first", size=1024
        )
        await service.create_transmission(
            port=7070, download_folder="/second", size=2048
        )

        transmissions = await service.get_transmission_list()
        assert len(transmissions) == 2
        # IDs should be auto-incremented integers
        assert transmissions[0].id >= 1
        assert transmissions[1].id > transmissions[0].id
