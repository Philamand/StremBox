from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi.testclient import TestClient

from main import app
from services.torrent_manager import TorrentManager
from utils.security import validate_bearer_token


@pytest.fixture(autouse=True)
def clear_overrides():
    """
    Ensure dependency overrides are cleared after each test to avoid leaking state
    between tests.
    """
    orig = app.dependency_overrides.copy()
    yield
    app.dependency_overrides.clear()
    app.dependency_overrides.update(orig)


def test_get_torrent_list_returns_manager_list():
    # Prepare a mocked TorrentManager whose get_torrent_list returns a JSON-serializable list
    mock_manager = MagicMock()
    mock_manager.get_torrent_list = AsyncMock(
        return_value=[{"hash": "h1", "name": "one"}, {"hash": "h2", "name": "two"}]
    )

    # Override dependencies: bypass auth and provide our mock manager
    app.dependency_overrides[validate_bearer_token] = lambda: None
    app.dependency_overrides[TorrentManager] = lambda: mock_manager

    with TestClient(app) as client:
        resp = client.get("/torrents/")

    assert resp.status_code == 200
    assert resp.json() == [{"hash": "h1", "name": "one"}, {"hash": "h2", "name": "two"}]


def test_get_torrent_hashes_returns_hash_list():
    # Prepare a mocked TorrentManager whose get_torrent_list returns objects with .hash
    mock_manager = MagicMock()
    mock_manager.get_torrent_list = AsyncMock(
        return_value=[SimpleNamespace(hash="hashA"), SimpleNamespace(hash="hashB")]
    )

    # Override dependencies: bypass auth and provide our mock manager
    app.dependency_overrides[validate_bearer_token] = lambda: None
    app.dependency_overrides[TorrentManager] = lambda: mock_manager

    with TestClient(app) as client:
        resp = client.get("/torrents/hashes/")

    assert resp.status_code == 200
    assert resp.json() == ["hashA", "hashB"]
