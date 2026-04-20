from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi import HTTPException

from services.torrent_manager import TorrentManager


@pytest.fixture
def mock_qb_client(monkeypatch):
    """
    Patch the qbittorrentapi.Client used inside services.torrent_manager.TorrentManager
    so no real network calls are made. Returns the mocked client instance so tests
    can configure return values / side effects.
    """
    mock_client_cls = MagicMock()
    mock_instance = MagicMock()
    mock_client_cls.return_value = mock_instance
    monkeypatch.setattr(
        "services.torrent_manager.qbittorrentapi.Client", mock_client_cls
    )
    return mock_instance


class TestTorrentManager:
    @pytest.mark.anyio
    async def test_add_torrent_missing_api_key_raises_http_exception(
        self, mock_qb_client
    ):
        manager = TorrentManager()
        with pytest.raises(HTTPException) as exc:
            await manager.add_torrent(
                hash="abc", tracker="c411", api_key=None, torrent_id=None
            )
        assert exc.value.status_code == 400
        assert "Clé API non configurée" in exc.value.detail

    @pytest.mark.anyio
    async def test_add_torrent_c411_builds_url_and_calls_torrents_add(
        self, mock_qb_client
    ):
        mock_qb_client.torrents_add = MagicMock(return_value="ok")
        manager = TorrentManager()
        result = await manager.add_torrent(
            hash="HASH123", tracker="c411", api_key="APIKEY", torrent_id=None
        )
        expected_url = "https://c411.org/api?t=get&id=HASH123&apikey=APIKEY"
        mock_qb_client.torrents_add.assert_called_once_with(
            urls=expected_url, is_sequential_download=True
        )
        assert result == "ok"

    @pytest.mark.anyio
    async def test_add_torrent_torr9_builds_url_and_calls_torrents_add(
        self, mock_qb_client
    ):
        mock_qb_client.torrents_add = MagicMock(return_value="ok2")
        manager = TorrentManager()
        result = await manager.add_torrent(
            hash="IGNORED", tracker="torr9", api_key="KEY", torrent_id="TID123"
        )
        expected_url = (
            "https://api.torr9.net/api/v1/torznab/torrents/TID123/download?passkey=KEY"
        )
        mock_qb_client.torrents_add.assert_called_once_with(
            urls=expected_url, is_sequential_download=True
        )
        assert result == "ok2"

    @pytest.mark.anyio
    async def test_add_torrent_unsupported_tracker_raises_http_exception(
        self, mock_qb_client
    ):
        manager = TorrentManager()
        with pytest.raises(HTTPException) as exc:
            await manager.add_torrent(
                hash="h", tracker="unknown", api_key="k", torrent_id=None
            )
        assert exc.value.status_code == 400
        assert "Tracker non supporté" in exc.value.detail

    @pytest.mark.anyio
    async def test_check_torrent_returns_true_and_false_based_on_client_response(
        self, mock_qb_client
    ):
        # First call returns a non-empty list -> True, second call empty -> False
        mock_qb_client.torrents_info = MagicMock(side_effect=[["t1"], []])
        manager = TorrentManager()
        res1 = await manager.check_torrent("h1")
        res2 = await manager.check_torrent("h2")
        assert res1 is True
        assert res2 is False
        assert mock_qb_client.torrents_info.call_count == 2

    @pytest.mark.anyio
    async def test_wait_until_added_succeeds_when_torrent_appears(self, mock_qb_client):
        # Simulate first poll empty, second poll has torrent
        mock_qb_client.torrents_info = MagicMock(side_effect=[[], ["found"]])
        manager = TorrentManager()
        # Use small timeout/poll_interval so test runs fast
        await manager.wait_until_added("h", timeout=1.0, poll_interval=0.01)
        assert mock_qb_client.torrents_info.call_count >= 2

    @pytest.mark.anyio
    async def test_wait_until_added_raises_on_timeout(self, mock_qb_client):
        # torrents_info always returns empty -> should timeout
        mock_qb_client.torrents_info = MagicMock(return_value=[])
        manager = TorrentManager()
        with pytest.raises(HTTPException) as exc:
            await manager.wait_until_added("h", timeout=0.05, poll_interval=0.01)
        assert exc.value.status_code == 504
        assert "Timed out" in exc.value.detail

    @pytest.mark.anyio
    async def test_get_torrent_files_and_list_return_client_values(
        self, mock_qb_client
    ):
        mock_files = ["file1", "file2"]
        mock_list = ["tinfo1", "tinfo2"]
        mock_qb_client.torrents_files = MagicMock(return_value=mock_files)
        mock_qb_client.torrents_info = MagicMock(return_value=mock_list)
        manager = TorrentManager()
        files = await manager.get_torrent_files("h")
        tlist = await manager.get_torrent_list()
        assert files == mock_files
        assert tlist == mock_list

    @pytest.mark.anyio
    async def test_ensure_torrent_available_noop_when_exists(self, mock_qb_client):
        manager = TorrentManager()
        manager.check_torrent = AsyncMock(return_value=True)  # type: ignore
        manager.add_torrent = AsyncMock()  # type: ignore
        manager.wait_until_added = AsyncMock()  # type: ignore
        await manager.ensure_torrent_available(
            "h", tracker=None, api_key=None, torrent_id=None
        )
        # When torrent exists, add_torrent and wait_until_added should not be called
        manager.add_torrent.assert_not_awaited()  # type: ignore
        manager.wait_until_added.assert_not_awaited()  # type: ignore

    @pytest.mark.anyio
    async def test_ensure_torrent_available_raises_when_not_found_and_no_tracker(
        self, mock_qb_client
    ):
        manager = TorrentManager()
        manager.check_torrent = AsyncMock(return_value=False)  # type: ignore
        with pytest.raises(HTTPException) as exc:
            await manager.ensure_torrent_available(
                "h", tracker=None, api_key=None, torrent_id=None
            )
        assert exc.value.status_code == 404
        assert "Torrent introuvable" in exc.value.detail

    @pytest.mark.anyio
    async def test_ensure_torrent_available_adds_and_waits_when_missing(
        self, mock_qb_client
    ):
        manager = TorrentManager()
        manager.check_torrent = AsyncMock(return_value=False)  # type: ignore
        manager.add_torrent = AsyncMock()  # type: ignore
        manager.wait_until_added = AsyncMock()  # type: ignore
        await manager.ensure_torrent_available(
            "HSH", tracker="c411", api_key="K", torrent_id=None
        )
        manager.add_torrent.assert_awaited_once_with("HSH", "c411", "K", None)  # type: ignore
        manager.wait_until_added.assert_awaited_once_with("HSH")  # type: ignore
