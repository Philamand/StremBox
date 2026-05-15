"""
Tests for the TorrentService class.

This file was AI-generated.
"""

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import Request
from transmission_rpc import File, Torrent

from torrents.services import TorrentService

# ---------------------------------------------------------------------------
# Helper to build a mock Request with the right transmission_data.
# ---------------------------------------------------------------------------


def _make_request(port: int = 9091) -> MagicMock:
    """Build a mock Request whose ``state.user`` carries valid transmission data."""
    request = MagicMock(spec=Request)
    request.state.user.transmission_data.port = port
    return request


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def mock_request():
    return _make_request()


# ---------------------------------------------------------------------------
# Constructor tests
# ---------------------------------------------------------------------------


class TestConstructor:
    """Tests for TorrentService.__init__."""

    def test_creates_client_with_transmission_port(self):
        """The client should be created using TRANSMISSION_URL and the user's port."""
        with patch("torrents.services.Client") as mock_cls:
            TorrentService(_make_request(port=1234))
            mock_cls.assert_called_once_with(
                host=mock_cls.call_args.kwargs.get("host"),
                port=1234,
            )

    def test_raises_when_transmission_data_is_none(self):
        """A ValueError is raised when the user has no transmission_data."""
        request = MagicMock(spec=Request)
        request.state.user.transmission_data = None
        with pytest.raises(ValueError, match="Transmission port is not set"):
            TorrentService(request)

    def test_raises_when_transmission_port_is_falsy(self):
        """A ValueError is raised when transmission_data.port is falsy."""
        request = _make_request(port=0)  # 0 is falsy
        with pytest.raises(ValueError, match="Transmission port is not set"):
            TorrentService(request)


# ---------------------------------------------------------------------------
# get_torrents
# ---------------------------------------------------------------------------


class TestGetTorrents:
    """Tests for TorrentService.get_torrents."""

    @pytest.mark.asyncio
    async def test_returns_torrent_list(self, mock_request):
        """get_torrents should return the list from the Transmission client."""
        fake_torrents = [
            MagicMock(spec=Torrent, id=1, name="ubuntu.iso"),
            MagicMock(spec=Torrent, id=2, name="debian.iso"),
        ]
        with patch("torrents.services.Client") as mock_cls:
            mock_cls.return_value.get_torrents.return_value = fake_torrents
            service = TorrentService(mock_request)
            result = await service.get_torrents()

        assert result is fake_torrents
        mock_cls.return_value.get_torrents.assert_called_once()

    @pytest.mark.asyncio
    async def test_returns_empty_list(self, mock_request):
        """Should handle an empty torrent list correctly."""
        with patch("torrents.services.Client") as mock_cls:
            mock_cls.return_value.get_torrents.return_value = []
            service = TorrentService(mock_request)
            result = await service.get_torrents()

        assert result == []


# ---------------------------------------------------------------------------
# add_torrent – bytes (torrent file content)
# ---------------------------------------------------------------------------


class TestAddTorrentBytes:
    """Tests for TorrentService.add_torrent when given a bytes input."""

    @pytest.mark.asyncio
    async def test_adds_when_within_size_limit(self, mock_request):
        """A .torrent file within the size limit should be added to Transmission."""
        torrent = b"some_torrent_data"
        max_size = 2_000_000
        with (
            patch("torrents.services.get_torrent_size", return_value=500_000),
            patch("torrents.services.Client") as mock_cls,
        ):
            service = TorrentService(mock_request)
            await service.add_torrent(torrent, max_size)

        mock_cls.return_value.add_torrent.assert_called_once_with(
            torrent=torrent, sequential_download=True
        )

    @pytest.mark.asyncio
    async def test_raises_when_size_exceeds_limit(self, mock_request):
        """Should raise ValueError without ever calling add_torrent."""
        torrent = b"large_torrent_data"
        max_size = 1024
        with (
            patch("torrents.services.get_torrent_size", return_value=2_000_000),
            patch("torrents.services.Client") as mock_cls,
        ):
            service = TorrentService(mock_request)
            with pytest.raises(
                ValueError,
                match="Pas assez d'espace disponible",
            ):
                await service.add_torrent(torrent, max_size)

        # The torrent should never have been added.
        mock_cls.return_value.add_torrent.assert_not_called()

    @pytest.mark.asyncio
    async def test_adds_when_size_equals_limit(self, mock_request):
        """When size equals max_size it should be accepted (not over limit)."""
        torrent = b"exact_size_torrent"
        max_size = 500_000
        with (
            patch("torrents.services.get_torrent_size", return_value=500_000),
            patch("torrents.services.Client") as mock_cls,
        ):
            service = TorrentService(mock_request)
            await service.add_torrent(torrent, max_size)

        mock_cls.return_value.add_torrent.assert_called_once()

    @pytest.mark.asyncio
    async def test_propagates_get_torrent_size_error(self, mock_request):
        """If get_torrent_size raises, the error should be propagated."""
        torrent = b"malformed_data"
        with (
            patch(
                "torrents.services.get_torrent_size",
                side_effect=ValueError("invalid torrent data"),
            ),
            patch("torrents.services.Client") as mock_cls,
        ):
            service = TorrentService(mock_request)
            with pytest.raises(ValueError, match="invalid torrent data"):
                await service.add_torrent(torrent, max_size=1_000_000)

        mock_cls.return_value.add_torrent.assert_not_called()


# ---------------------------------------------------------------------------
# add_torrent – str (magnet / URL)
# ---------------------------------------------------------------------------


class TestAddTorrentStr:
    """Tests for TorrentService.add_torrent when given a string input."""

    MAGNET = "magnet:?xt=urn:btih:ABCDEF1234567890ABCDEF1234567890ABCDEF12"

    @pytest.mark.asyncio
    async def test_adds_paused_and_starts_when_size_ok(self, mock_request):
        """Torrent is added paused, size is polled, then it's started."""
        fake_torrent = MagicMock(spec=Torrent)
        fake_torrent.hashString = "abc123"
        # First poll: metadata not ready yet (total_size = 0)
        # Second poll: metadata ready
        fake_size_torrent = MagicMock(spec=Torrent)
        fake_size_torrent.total_size = 500_000

        with patch("torrents.services.Client") as mock_cls:
            mock_cls.return_value.add_torrent.return_value = fake_torrent
            mock_cls.return_value.get_torrent.side_effect = [
                MagicMock(spec=Torrent, total_size=0),  # first poll
                fake_size_torrent,  # second poll
            ]

            service = TorrentService(mock_request)
            await service.add_torrent(self.MAGNET, max_size=2_000_000)

        # Added paused
        mock_cls.return_value.add_torrent.assert_called_once_with(
            torrent=self.MAGNET, paused=True, sequential_download=True
        )
        # Started after size check
        mock_cls.return_value.start_torrent.assert_called_once_with("abc123")
        # Never removed
        mock_cls.return_value.remove_torrent.assert_not_called()

    @pytest.mark.asyncio
    async def test_removes_when_size_exceeds_limit(self, mock_request):
        """Torrent is removed when its total size exceeds max_size."""
        fake_torrent = MagicMock(spec=Torrent)
        fake_torrent.hashString = "abc123"

        with patch("torrents.services.Client") as mock_cls:
            mock_cls.return_value.add_torrent.return_value = fake_torrent
            mock_cls.return_value.get_torrent.return_value = MagicMock(
                spec=Torrent,
                total_size=5_000_000,  # 5 MB > 1 MB limit
            )

            service = TorrentService(mock_request)
            with pytest.raises(
                ValueError,
                match="Pas assez d'espace disponible",
            ):
                await service.add_torrent(self.MAGNET, max_size=1_000_000)

        # Must have been removed with data deletion
        mock_cls.return_value.remove_torrent.assert_called_once_with(
            "abc123", delete_data=True
        )
        # Must never have been started
        mock_cls.return_value.start_torrent.assert_not_called()

    @pytest.mark.asyncio
    async def test_removes_on_metadata_timeout(self, mock_request):
        """When total_size stays 0 for too long, remove the torrent and raise."""
        fake_torrent = MagicMock(spec=Torrent)
        fake_torrent.hashString = "abc123"

        with patch("torrents.services.Client") as mock_cls:
            mock_cls.return_value.add_torrent.return_value = fake_torrent
            # Always returns total_size = 0  –  metadata never arrives
            mock_cls.return_value.get_torrent.return_value = MagicMock(
                spec=Torrent, total_size=0
            )

            service = TorrentService(mock_request)
            # Mock wait_for to immediately raise TimeoutError (avoids real 60s wait).
            # Note: this abandons the _poll_size coroutine, producing a benign
            # RuntimeWarning during garbage collection.
            with patch(
                "asyncio.wait_for",
                side_effect=asyncio.TimeoutError(),
            ):
                with pytest.raises(
                    ValueError,
                    match="Temps expiré",
                ):
                    await service.add_torrent(self.MAGNET, max_size=1_000_000)

        # Must have been removed
        mock_cls.return_value.remove_torrent.assert_called_once_with(
            "abc123", delete_data=True
        )
        mock_cls.return_value.start_torrent.assert_not_called()

    @pytest.mark.asyncio
    async def test_starts_immediately_when_metadata_already_available(
        self,
        mock_request,
    ):
        """If total_size > 0 on the first poll, start right away."""
        fake_torrent = MagicMock(spec=Torrent)
        fake_torrent.hashString = "abc123"

        with patch("torrents.services.Client") as mock_cls:
            mock_cls.return_value.add_torrent.return_value = fake_torrent
            mock_cls.return_value.get_torrent.return_value = MagicMock(
                spec=Torrent, total_size=200_000
            )

            service = TorrentService(mock_request)
            await service.add_torrent(self.MAGNET, max_size=1_000_000)

        mock_cls.return_value.start_torrent.assert_called_once_with("abc123")
        mock_cls.return_value.remove_torrent.assert_not_called()

    @pytest.mark.asyncio
    async def test_polls_until_metadata_available(self, mock_request):
        """Simulate a few zero-size polls before metadata becomes available."""
        fake_torrent = MagicMock(spec=Torrent)
        fake_torrent.hashString = "abc123"

        with patch("torrents.services.Client") as mock_cls:
            mock_cls.return_value.add_torrent.return_value = fake_torrent
            # Three polls: 0, 0, then finally the real size
            mock_cls.return_value.get_torrent.side_effect = [
                MagicMock(spec=Torrent, total_size=0),
                MagicMock(spec=Torrent, total_size=0),
                MagicMock(spec=Torrent, total_size=300_000),
            ]

            service = TorrentService(mock_request)
            with patch("asyncio.sleep", new_callable=AsyncMock) as mock_sleep:
                await service.add_torrent(self.MAGNET, max_size=1_000_000)

        # sleep should have been called twice (after the two zero-size polls)
        assert mock_sleep.call_count == 2
        mock_cls.return_value.start_torrent.assert_called_once_with("abc123")


# ---------------------------------------------------------------------------
# remove_torrent
# ---------------------------------------------------------------------------


class TestRemoveTorrent:
    """Tests for TorrentService.remove_torrent."""

    @pytest.mark.asyncio
    async def test_removes_without_deleting_files(self, mock_request):
        """Default behaviour: keep data on disk."""
        with patch("torrents.services.Client") as mock_cls:
            service = TorrentService(mock_request)
            await service.remove_torrent("hash123")

        mock_cls.return_value.remove_torrent.assert_called_once_with(
            "hash123", delete_data=False
        )

    @pytest.mark.asyncio
    async def test_removes_and_deletes_files(self, mock_request):
        """When delete_files=True, data should be deleted."""
        with patch("torrents.services.Client") as mock_cls:
            service = TorrentService(mock_request)
            await service.remove_torrent("hash456", delete_files=True)

        mock_cls.return_value.remove_torrent.assert_called_once_with(
            "hash456", delete_data=True
        )


# ---------------------------------------------------------------------------
# get_torrent_files
# ---------------------------------------------------------------------------


class TestGetTorrentFiles:
    """Tests for TorrentService.get_torrent_files."""

    @pytest.mark.asyncio
    async def test_returns_file_list(self, mock_request):
        """Should return the files of a specific torrent."""
        fake_files = [
            MagicMock(spec=File, name="video.mp4", size=1_000_000),
            MagicMock(spec=File, name="subs.srt", size=5_000),
        ]
        fake_torrent = MagicMock(spec=Torrent)
        fake_torrent.get_files.return_value = fake_files

        with patch("torrents.services.Client") as mock_cls:
            mock_cls.return_value.get_torrent.return_value = fake_torrent
            service = TorrentService(mock_request)
            result = await service.get_torrent_files("hash789")

        mock_cls.return_value.get_torrent.assert_called_once_with("hash789")
        fake_torrent.get_files.assert_called_once()
        assert result is fake_files

    @pytest.mark.asyncio
    async def test_returns_empty_file_list(self, mock_request):
        """Should handle a torrent with no files."""
        fake_torrent = MagicMock(spec=Torrent)
        fake_torrent.get_files.return_value = []

        with patch("torrents.services.Client") as mock_cls:
            mock_cls.return_value.get_torrent.return_value = fake_torrent
            service = TorrentService(mock_request)
            result = await service.get_torrent_files("hash_empty")

        assert result == []
