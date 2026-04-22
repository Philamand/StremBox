from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import HTTPException, Request

from utils.streams import (
    build_stream_headers,
    check_season_episode,
    parse_range,
    range_file_reader,
    resolve_file_path,
)


class TestParseRange:
    """Test suite for the parse_range function."""

    def test_parse_range_valid_start_and_end(self):
        """Test parsing a valid range with both start and end."""
        start, end = parse_range("bytes=0-499")
        assert start == 0
        assert end == 499

    def test_parse_range_valid_start_only(self):
        """Test parsing a valid range with only a start."""
        start, end = parse_range("bytes=500-")
        assert start == 500
        assert end is None

    def test_parse_range_valid_end_only(self):
        """Test parsing a valid range with only an end."""
        start, end = parse_range("bytes=-100")
        assert start is None
        assert end == 100

    def test_parse_range_empty(self):
        """Test parsing an empty range."""
        start, end = parse_range("bytes=")
        assert start is None
        assert end is None

    def test_parse_range_invalid_unit(self):
        """Test parsing a range with an invalid unit."""
        start, end = parse_range("invalid=0-499")
        assert start is None
        assert end is None

    def test_parse_range_malformed(self):
        """Test parsing a malformed range."""
        start, end = parse_range("bytes=invalid")
        assert start is None
        assert end is None

    def test_parse_range_none(self):
        """Test parsing a None header."""
        start, end = parse_range(None)
        assert start is None
        assert end is None

    def test_parse_range_empty_string(self):
        """Test parsing an empty string."""
        start, end = parse_range("")
        assert start is None
        assert end is None

    def test_parse_range_negative_values(self):
        """Test parsing a range with negative values."""
        start, end = parse_range("bytes=-500-1000")
        assert start is None
        assert end is None

    def test_parse_range_non_numeric(self):
        """Test parsing a range with non-numeric values."""
        start, end = parse_range("bytes=abc-def")
        assert start is None
        assert end is None

    def test_parse_range_missing_separator(self):
        """Test parsing a range with a missing separator."""
        start, end = parse_range("bytes=0")
        assert start is None
        assert end is None

    def test_parse_range_extra_equals(self):
        """Test parsing a range with extra equals signs."""
        start, end = parse_range("bytes=0-499-extra")
        assert start is None
        assert end is None

    def test_parse_range_whitespace(self):
        """Test parsing a range with whitespace."""
        start, end = parse_range("bytes= 0 - 499 ")
        assert start == 0
        assert end == 499

    def test_parse_range_large_numbers(self):
        """Test parsing a range with large numbers."""
        start, end = parse_range("bytes=1000000-9999999")
        assert start == 1000000
        assert end == 9999999

    def test_parse_range_zero_values(self):
        """Test parsing a range with zero values."""
        start, end = parse_range("bytes=0-0")
        assert start == 0
        assert end == 0


class TestCheckSeasonEpisode:
    """Test suite for the check_season_episode function."""

    def test_check_season_episode_season_episode_format(self):
        """Test parsing S##E## format."""
        assert check_season_episode("show.S01E05.mkv", 1, 5) is True
        assert check_season_episode("show.S01E05.mkv", 1, 6) is False
        assert check_season_episode("show.S02E03.mkv", 2, 3) is True
        assert check_season_episode("show.S02E03.mkv", 1, 3) is False

    def test_check_season_episode_saison_format(self):
        """Test parsing SAISON##E## format (French)."""
        assert check_season_episode("show.SAISON01E05.mkv", 1, 5) is True
        assert check_season_episode("show.SAISON02E10.mkv", 2, 10) is True
        assert check_season_episode("show.SAISON01E05.mkv", 2, 5) is False

    def test_check_season_episode_case_insensitive(self):
        """Test that season/episode parsing is case insensitive."""
        assert check_season_episode("show.s01e05.mkv", 1, 5) is True
        assert check_season_episode("show.SEASON01E05.mkv", 1, 5) is True
        assert check_season_episode("show.season01e05.mkv", 1, 5) is True

    def test_check_season_episode_with_separators(self):
        """Test various separator formats."""
        assert check_season_episode("show.S01-E05.mkv", 1, 5) is True
        assert check_season_episode("show.S01_E05.mkv", 1, 5) is True
        assert check_season_episode("show.S01.E05.mkv", 1, 5) is True

    def test_check_season_episode_x_format(self):
        """Test parsing ##x## format."""
        assert check_season_episode("show.01x05.mkv", 1, 5) is True
        assert check_season_episode("show.02x10.mkv", 2, 10) is True
        assert check_season_episode("show.01x05.mkv", 2, 5) is False

    def test_check_season_episode_season_only(self):
        """Test parsing season-only format."""
        assert check_season_episode("show.S01.mkv", 1, 5) is True
        assert check_season_episode("show.SEASON02.mkv", 2, 3) is True
        assert check_season_episode("show.S01.mkv", 2, 5) is False

    def test_check_season_episode_episode_range(self):
        """Test parsing episode ranges (E##-##)."""
        assert check_season_episode("show.S01E05-E10.mkv", 1, 7) is True
        assert check_season_episode("show.S01E05-E10.mkv", 1, 5) is True
        assert check_season_episode("show.S01E05-E10.mkv", 1, 10) is True
        assert check_season_episode("show.S01E05-E10.mkv", 1, 11) is False
        assert check_season_episode("show.S01E05-E10.mkv", 1, 4) is False

    def test_check_season_episode_no_match(self):
        """Test files with no season/episode information."""
        assert check_season_episode("random_movie.mkv", 1, 5) is False
        assert check_season_episode("some.file.without.format", 1, 1) is False

    def test_check_season_episode_large_numbers(self):
        """Test parsing large season/episode numbers."""
        assert check_season_episode("show.S10E25.mkv", 10, 25) is True
        assert check_season_episode("show.10x25.mkv", 10, 25) is True
        assert check_season_episode("show.S99E99.mkv", 99, 99) is True

    def test_check_season_episode_multiple_matches(self):
        """Test files with multiple season/episode patterns."""
        assert check_season_episode("S01E05.and.S02E10.mkv", 1, 5) is True
        assert check_season_episode("S01E05.and.S02E10.mkv", 2, 10) is True
        assert check_season_episode("S01E05.and.S02E10.mkv", 3, 5) is False

    def test_check_season_episode_mixed_separators(self):
        """Test mixed separator styles."""
        assert check_season_episode("show.S01_E05.mkv", 1, 5) is True
        assert check_season_episode("show.S01.E05.mkv", 1, 5) is True


class TestResolveFilePath:
    """Test suite for the resolve_file_path function."""

    @patch("utils.streams.os.path.isfile")
    def test_resolve_file_path_plain_file_exists(self, mock_isfile):
        """Test resolving a plain file that exists."""
        mock_isfile.return_value = True
        result = resolve_file_path("video.mp4", None, None)
        assert "video.mp4" in result
        mock_isfile.assert_called_once()

    @patch("utils.streams.os.path.isfile")
    def test_resolve_file_path_plain_file_not_found(self, mock_isfile):
        """Test resolving a plain file that does not exist."""
        mock_isfile.return_value = False
        with pytest.raises(HTTPException) as exc_info:
            resolve_file_path("nonexistent.mp4", None, None)
        assert exc_info.value.status_code == 404

    @patch("utils.streams.os.path.isdir")
    @patch("utils.streams.os.listdir")
    @patch("utils.streams.check_season_episode")
    def test_resolve_file_path_season_episode_found(
        self, mock_check, mock_listdir, mock_isdir
    ):
        """Test resolving a file with season/episode that matches."""
        mock_isdir.return_value = True
        mock_listdir.return_value = ["S01E05.mkv", "S01E06.mkv"]
        mock_check.side_effect = lambda f, s, e: f == "S01E05.mkv"

        result = resolve_file_path("series/", 1, 5)
        assert "S01E05.mkv" in result
        mock_isdir.assert_called_once()

    @patch("utils.streams.os.path.isdir")
    def test_resolve_file_path_season_episode_dir_not_found(self, mock_isdir):
        """Test resolving with season/episode when directory does not exist."""
        mock_isdir.return_value = False
        with pytest.raises(HTTPException) as exc_info:
            resolve_file_path("nonexistent/", 1, 5)
        assert exc_info.value.status_code == 404

    @patch("utils.streams.os.path.isdir")
    @patch("utils.streams.os.listdir")
    @patch("utils.streams.check_season_episode")
    def test_resolve_file_path_season_episode_no_match(
        self, mock_check, mock_listdir, mock_isdir
    ):
        """Test resolving with season/episode when no file matches."""
        mock_isdir.return_value = True
        mock_listdir.return_value = ["S01E05.mkv", "S01E06.mkv"]
        mock_check.return_value = False

        with pytest.raises(HTTPException) as exc_info:
            resolve_file_path("series/", 2, 10)
        assert exc_info.value.status_code == 404

    @patch("utils.streams.os.path.isdir")
    @patch("utils.streams.os.listdir")
    @patch("utils.streams.check_season_episode")
    def test_resolve_file_path_multiple_files_first_match(
        self, mock_check, mock_listdir, mock_isdir
    ):
        """Test that the first matching file is returned."""
        mock_isdir.return_value = True
        mock_listdir.return_value = ["S01E05.mkv", "S02E05.mkv", "S01E05_alt.mkv"]

        def check_side_effect(f, s, e):
            return s == 1 and e == 5

        mock_check.side_effect = check_side_effect

        result = resolve_file_path("series/", 1, 5)
        # Should return the first match
        assert "S01E05.mkv" in result

    @patch("utils.streams.os.path.isdir")
    @patch("utils.streams.os.listdir")
    @patch("utils.streams.check_season_episode")
    def test_resolve_file_path_empty_directory(
        self, mock_check, mock_listdir, mock_isdir
    ):
        """Test resolving when directory is empty."""
        mock_isdir.return_value = True
        mock_listdir.return_value = []

        with pytest.raises(HTTPException) as exc_info:
            resolve_file_path("series/", 1, 5)
        assert exc_info.value.status_code == 404

    @patch("utils.streams.os.path.isfile")
    def test_resolve_file_path_with_subdirectory(self, mock_isfile):
        """Test resolving a file in a subdirectory."""
        mock_isfile.return_value = True
        result = resolve_file_path("movies/action/video.mp4", None, None)
        assert "movies/action/video.mp4" in result

    @patch("utils.streams.os.path.isfile")
    def test_resolve_file_path_season_without_episode(self, mock_isfile):
        """Test that season/episode resolution requires both season and episode."""
        mock_isfile.return_value = False

        # When season is not None but episode is None, it tries isfile
        with pytest.raises(HTTPException):
            resolve_file_path("series/", 1, None)

    @patch("utils.streams.os.path.isdir")
    @patch("utils.streams.os.listdir")
    @patch("utils.streams.check_season_episode")
    def test_resolve_file_path_special_characters_in_filename(
        self, mock_check, mock_listdir, mock_isdir
    ):
        """Test resolving files with special characters."""
        mock_isdir.return_value = True
        mock_listdir.return_value = ["Show.Name.S01E05.[1080p].mkv"]
        mock_check.side_effect = lambda f, s, e: f == "Show.Name.S01E05.[1080p].mkv"

        result = resolve_file_path("series/", 1, 5)
        assert "Show.Name.S01E05.[1080p].mkv" in result

    @patch("utils.streams.os.path.isdir")
    @patch("utils.streams.os.listdir")
    @patch("utils.streams.check_season_episode")
    def test_resolve_file_path_unicode_filenames(
        self, mock_check, mock_listdir, mock_isdir
    ):
        """Test resolving files with unicode characters."""
        mock_isdir.return_value = True
        mock_listdir.return_value = ["日本語.S01E05.mkv"]
        mock_check.side_effect = lambda f, s, e: f == "日本語.S01E05.mkv"

        result = resolve_file_path("series/", 1, 5)
        assert "日本語.S01E05.mkv" in result


class TestBuildStreamHeaders:
    """Test suite for the build_stream_headers function."""

    def test_build_stream_headers_mp4_no_range(self):
        """Test building headers for MP4 file without range."""
        headers, status_code = build_stream_headers("video.mp4", None, 0, 999, 1000)

        assert status_code == 200
        assert headers["content-type"] == "video/mp4"
        assert headers["accept-ranges"] == "bytes"
        assert headers["content-length"] == "1000"
        assert "content-range" not in headers

    def test_build_stream_headers_mkv_no_range(self):
        """Test building headers for MKV file without range."""
        headers, status_code = build_stream_headers("video.mkv", None, 0, 999, 5000)

        assert status_code == 200
        assert headers["content-type"] == "video/x-matroska"
        assert headers["content-length"] == "5000"

    def test_build_stream_headers_webm_no_range(self):
        """Test building headers for WebM file without range."""
        headers, status_code = build_stream_headers("video.webm", None, 0, 999, 2000)

        assert status_code == 200
        assert headers["content-type"] == "video/webm"
        assert headers["content-length"] == "2000"

    def test_build_stream_headers_with_range(self):
        """Test building headers for partial range request."""
        headers, status_code = build_stream_headers(
            "video.mp4", "bytes=0-499", 0, 499, 1000
        )

        assert status_code == 206
        assert headers["content-type"] == "video/mp4"
        assert headers["content-range"] == "bytes 0-499/1000"
        assert headers["content-length"] == "500"
        assert headers["accept-ranges"] == "bytes"

    def test_build_stream_headers_with_range_middle(self):
        """Test building headers for range in the middle of file."""
        headers, status_code = build_stream_headers(
            "video.mp4", "bytes=500-999", 500, 999, 1000
        )

        assert status_code == 206
        assert headers["content-range"] == "bytes 500-999/1000"
        assert headers["content-length"] == "500"

    def test_build_stream_headers_with_range_end(self):
        """Test building headers for range at end of file."""
        headers, status_code = build_stream_headers(
            "video.mp4", "bytes=900-999", 900, 999, 1000
        )

        assert status_code == 206
        assert headers["content-range"] == "bytes 900-999/1000"
        assert headers["content-length"] == "100"

    def test_build_stream_headers_single_byte_range(self):
        """Test building headers for single byte range."""
        headers, status_code = build_stream_headers(
            "video.mp4", "bytes=500-500", 500, 500, 1000
        )

        assert status_code == 206
        assert headers["content-range"] == "bytes 500-500/1000"
        assert headers["content-length"] == "1"

    def test_build_stream_headers_large_file(self):
        """Test building headers for large file."""
        large_size = 1024 * 1024 * 1024  # 1GB
        headers, status_code = build_stream_headers(
            "video.mp4", None, 0, large_size - 1, large_size
        )

        assert status_code == 200
        assert headers["content-length"] == str(large_size)

    def test_build_stream_headers_large_file_with_range(self):
        """Test building headers for large file with range."""
        large_size = 1024 * 1024 * 1024  # 1GB
        start = 500 * 1024 * 1024  # 500MB
        end = 600 * 1024 * 1024  # 600MB

        headers, status_code = build_stream_headers(
            "video.mp4", "bytes=500-600", start, end, large_size
        )

        assert status_code == 206
        assert headers["content-range"] == f"bytes {start}-{end}/{large_size}"

    def test_build_stream_headers_all_video_formats(self):
        """Test building headers for all supported video formats."""
        formats = {
            ".mp4": "video/mp4",
            ".mkv": "video/x-matroska",
            ".webm": "video/webm",
            ".avi": "video/x-msvideo",
            ".mov": "video/quicktime",
            ".flv": "video/x-flv",
            ".wmv": "video/x-ms-wmv",
            ".m3u8": "application/vnd.apple.mpegurl",
            ".ts": "video/mp2t",
            ".mpg": "video/mpeg",
            ".mpeg": "video/mpeg",
            ".3gp": "video/3gpp",
            ".ogv": "video/ogg",
        }

        for ext, mime_type in formats.items():
            headers, status_code = build_stream_headers(
                f"video{ext}", None, 0, 999, 1000
            )
            assert headers["content-type"] == mime_type
            assert status_code == 200

    def test_build_stream_headers_uppercase_extension(self):
        """Test building headers for file with uppercase extension."""
        headers, status_code = build_stream_headers("VIDEO.MP4", None, 0, 999, 1000)

        assert status_code == 200
        assert headers["content-type"] == "video/mp4"

    def test_build_stream_headers_mixed_case_extension(self):
        """Test building headers for file with mixed case extension."""
        headers, status_code = build_stream_headers("Video.MkV", None, 0, 999, 1000)

        assert status_code == 200
        assert headers["content-type"] == "video/x-matroska"

    def test_build_stream_headers_unsupported_format(self):
        """Test building headers for unsupported file format."""
        with pytest.raises(ValueError) as exc_info:
            build_stream_headers("document.pdf", None, 0, 999, 1000)

        assert "Unsupported file format" in str(exc_info.value)
        assert ".pdf" in str(exc_info.value)

    def test_build_stream_headers_unsupported_audio_format(self):
        """Test building headers for unsupported audio format."""
        with pytest.raises(ValueError) as exc_info:
            build_stream_headers("audio.mp3", None, 0, 999, 1000)

        assert "Unsupported file format" in str(exc_info.value)

    def test_build_stream_headers_no_extension(self):
        """Test building headers for file with no extension."""
        with pytest.raises(ValueError) as exc_info:
            build_stream_headers("videofile", None, 0, 999, 1000)

        assert "Unsupported file format" in str(exc_info.value)

    def test_build_stream_headers_range_calculations(self):
        """Test that content-length calculation is correct for ranges."""
        # Range: bytes 100-199 (100 bytes)
        headers, _ = build_stream_headers("video.mp4", "bytes=100-199", 100, 199, 1000)
        assert headers["content-length"] == "100"

        # Range: bytes 0-99 (100 bytes)
        headers, _ = build_stream_headers("video.mp4", "bytes=0-99", 0, 99, 1000)
        assert headers["content-length"] == "100"

        # Range: bytes 1000-1999 (1000 bytes)
        headers, _ = build_stream_headers(
            "video.mp4", "bytes=1000-1999", 1000, 1999, 5000
        )
        assert headers["content-length"] == "1000"

    def test_build_stream_headers_common_mime_types(self):
        """Test that common video MIME types are correctly assigned."""
        test_cases = [
            ("video.mp4", "video/mp4"),
            ("movie.mkv", "video/x-matroska"),
            ("clip.webm", "video/webm"),
            ("stream.m3u8", "application/vnd.apple.mpegurl"),
        ]

        for file_path, expected_mime in test_cases:
            headers, _ = build_stream_headers(file_path, None, 0, 999, 1000)
            assert headers["content-type"] == expected_mime

    def test_build_stream_headers_accept_ranges_always_present(self):
        """Test that accept-ranges header is always present."""
        # Without range
        headers, _ = build_stream_headers("video.mp4", None, 0, 999, 1000)
        assert headers["accept-ranges"] == "bytes"

        # With range
        headers, _ = build_stream_headers("video.mp4", "bytes=0-499", 0, 499, 1000)
        assert headers["accept-ranges"] == "bytes"

    def test_build_stream_headers_path_with_spaces(self):
        """Test building headers for file path with spaces."""
        headers, status_code = build_stream_headers(
            "my video file.mp4", None, 0, 999, 1000
        )

        assert status_code == 200
        assert headers["content-type"] == "video/mp4"

    def test_build_stream_headers_path_with_special_chars(self):
        """Test building headers for file path with special characters."""
        headers, status_code = build_stream_headers(
            "/path/to/video-2024[1080p].mkv", None, 0, 999, 1000
        )

        assert status_code == 200
        assert headers["content-type"] == "video/x-matroska"

    def test_build_stream_headers_status_codes(self):
        """Test that correct status codes are returned."""
        # 200 for full file
        _, status = build_stream_headers("video.mp4", None, 0, 999, 1000)
        assert status == 200

        # 206 for range request
        _, status = build_stream_headers("video.mp4", "bytes=0-499", 0, 499, 1000)
        assert status == 206


class MockAsyncFile:
    """Mock async file object for testing."""

    def __init__(self, data: bytes):
        self.data = data
        self.pos = 0
        self.seek = AsyncMock(side_effect=self._seek_impl)
        self.read = AsyncMock(side_effect=self._read_impl)

    async def _seek_impl(self, offset: int):
        """Implementation of seek operation."""
        self.pos = offset

    async def _read_impl(self, size: int) -> bytes:
        """Implementation of read operation."""
        data = self.data[self.pos : self.pos + size]
        self.pos += len(data)
        return data

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        pass


class TestRangeFileReader:
    """Test suite for the range_file_reader function."""

    @pytest.fixture
    def mock_request(self):
        """Create a mock Request object."""
        request = MagicMock(spec=Request)
        request.is_disconnected = AsyncMock(return_value=False)
        return request

    @pytest.fixture
    def test_data(self):
        """Create test data for file content."""
        return b"0123456789" * 100  # 1000 bytes

    async def collect_chunks(self, generator):
        """Helper to collect all chunks from async generator."""
        return [chunk async for chunk in generator]

    @patch("utils.streams.aiofiles.open")
    @pytest.mark.anyio
    async def test_range_file_reader_basic(self, mock_open, mock_request, test_data):
        """Test basic file reading from start to end."""
        mock_file = MockAsyncFile(test_data)
        mock_open.return_value.__aenter__ = AsyncMock(return_value=mock_file)
        mock_open.return_value.__aexit__ = AsyncMock(return_value=None)

        chunks = await self.collect_chunks(
            range_file_reader(mock_request, "test.txt", start=0, chunk_size=100)
        )

        assert b"".join(chunks) == test_data
        mock_file.seek.assert_called_once_with(0)

    @patch("utils.streams.aiofiles.open")
    @pytest.mark.anyio
    async def test_range_file_reader_with_end(self, mock_open, mock_request, test_data):
        """Test reading with both start and end specified."""
        mock_file = MockAsyncFile(test_data)
        mock_open.return_value.__aenter__ = AsyncMock(return_value=mock_file)
        mock_open.return_value.__aexit__ = AsyncMock(return_value=None)

        chunks = await self.collect_chunks(
            range_file_reader(
                mock_request, "test.txt", start=100, end=199, chunk_size=50
            )
        )

        expected = test_data[100:200]
        assert b"".join(chunks) == expected

    @patch("utils.streams.aiofiles.open")
    @pytest.mark.anyio
    async def test_range_file_reader_start_only(
        self, mock_open, mock_request, test_data
    ):
        """Test reading from start to end of file."""
        mock_file = MockAsyncFile(test_data)
        mock_open.return_value.__aenter__ = AsyncMock(return_value=mock_file)
        mock_open.return_value.__aexit__ = AsyncMock(return_value=None)

        chunks = await self.collect_chunks(
            range_file_reader(mock_request, "test.txt", start=50, chunk_size=50)
        )

        expected = test_data[50:]
        assert b"".join(chunks) == expected

    @patch("utils.streams.aiofiles.open")
    @pytest.mark.anyio
    async def test_range_file_reader_respects_chunk_size(
        self, mock_open, mock_request, test_data
    ):
        """Test that chunks are of specified size."""
        mock_file = MockAsyncFile(test_data)
        mock_open.return_value.__aenter__ = AsyncMock(return_value=mock_file)
        mock_open.return_value.__aexit__ = AsyncMock(return_value=None)

        chunks = await self.collect_chunks(
            range_file_reader(mock_request, "test.txt", start=0, chunk_size=10)
        )

        for i, chunk in enumerate(chunks[:-1]):
            assert len(chunk) == 10
        assert len(chunks) == 100

    @patch("utils.streams.aiofiles.open")
    @pytest.mark.anyio
    async def test_range_file_reader_custom_chunk_size(
        self, mock_open, mock_request, test_data
    ):
        """Test with custom chunk size."""
        mock_file = MockAsyncFile(test_data)
        mock_open.return_value.__aenter__ = AsyncMock(return_value=mock_file)
        mock_open.return_value.__aexit__ = AsyncMock(return_value=None)

        chunks = await self.collect_chunks(
            range_file_reader(mock_request, "test.txt", start=0, end=99, chunk_size=25)
        )

        for chunk in chunks[:-1]:
            assert len(chunk) == 25
        assert len(chunks[-1]) == 25

    @patch("utils.streams.aiofiles.open")
    @pytest.mark.anyio
    async def test_range_file_reader_disconnected_request(
        self, mock_open, mock_request, test_data
    ):
        """Test that reading stops when request is disconnected."""
        mock_file = MockAsyncFile(test_data)
        mock_open.return_value.__aenter__ = AsyncMock(return_value=mock_file)
        mock_open.return_value.__aexit__ = AsyncMock(return_value=None)

        mock_request.is_disconnected = AsyncMock(
            side_effect=[False, False, True, False]
        )

        chunks = await self.collect_chunks(
            range_file_reader(mock_request, "test.txt", start=0, chunk_size=100)
        )

        assert len(chunks) == 2

    @patch("utils.streams.aiofiles.open")
    @pytest.mark.anyio
    async def test_range_file_reader_empty_range(
        self, mock_open, mock_request, test_data
    ):
        """Test reading with start > end (empty range)."""
        mock_file = MockAsyncFile(test_data)
        mock_open.return_value.__aenter__ = AsyncMock(return_value=mock_file)
        mock_open.return_value.__aexit__ = AsyncMock(return_value=None)

        chunks = await self.collect_chunks(
            range_file_reader(
                mock_request, "test.txt", start=500, end=499, chunk_size=100
            )
        )

        assert len(chunks) == 0

    @patch("utils.streams.aiofiles.open")
    @pytest.mark.anyio
    async def test_range_file_reader_start_equals_end(
        self, mock_open, mock_request, test_data
    ):
        """Test reading a single byte."""
        mock_file = MockAsyncFile(test_data)
        mock_open.return_value.__aenter__ = AsyncMock(return_value=mock_file)
        mock_open.return_value.__aexit__ = AsyncMock(return_value=None)

        chunks = await self.collect_chunks(
            range_file_reader(
                mock_request, "test.txt", start=100, end=100, chunk_size=100
            )
        )

        assert len(chunks) == 1
        assert chunks[0] == test_data[100:101]

    @patch("utils.streams.aiofiles.open")
    @pytest.mark.anyio
    async def test_range_file_reader_end_exceeds_file_size(
        self, mock_open, mock_request, test_data
    ):
        """Test reading when end exceeds file size."""
        mock_file = MockAsyncFile(test_data)
        mock_open.return_value.__aenter__ = AsyncMock(return_value=mock_file)
        mock_open.return_value.__aexit__ = AsyncMock(return_value=None)

        chunks = await self.collect_chunks(
            range_file_reader(
                mock_request, "test.txt", start=0, end=999999, chunk_size=100
            )
        )

        assert b"".join(chunks) == test_data

    @patch("utils.streams.aiofiles.open")
    @pytest.mark.anyio
    async def test_range_file_reader_start_beyond_file(
        self, mock_open, mock_request, test_data
    ):
        """Test reading when start is beyond file size."""
        mock_file = MockAsyncFile(test_data)
        mock_open.return_value.__aenter__ = AsyncMock(return_value=mock_file)
        mock_open.return_value.__aexit__ = AsyncMock(return_value=None)

        chunks = await self.collect_chunks(
            range_file_reader(mock_request, "test.txt", start=999999, chunk_size=100)
        )

        assert len(chunks) == 0

    @patch("utils.streams.aiofiles.open")
    @pytest.mark.anyio
    async def test_range_file_reader_zero_chunk_size(
        self, mock_open, mock_request, test_data
    ):
        """Test with chunk size of 1."""
        data = b"0123456789"
        mock_file = MockAsyncFile(data)
        mock_open.return_value.__aenter__ = AsyncMock(return_value=mock_file)
        mock_open.return_value.__aexit__ = AsyncMock(return_value=None)

        chunks = await self.collect_chunks(
            range_file_reader(mock_request, "test.txt", start=0, chunk_size=1)
        )

        assert len(chunks) == 10
        assert b"".join(chunks) == data

    @patch("utils.streams.aiofiles.open")
    @pytest.mark.anyio
    async def test_range_file_reader_large_chunk_size(
        self, mock_open, mock_request, test_data
    ):
        """Test with chunk size larger than remaining data."""
        mock_file = MockAsyncFile(test_data)
        mock_open.return_value.__aenter__ = AsyncMock(return_value=mock_file)
        mock_open.return_value.__aexit__ = AsyncMock(return_value=None)

        chunks = await self.collect_chunks(
            range_file_reader(mock_request, "test.txt", start=0, chunk_size=5000)
        )

        assert len(chunks) == 1
        assert chunks[0] == test_data

    @patch("utils.streams.aiofiles.open")
    @pytest.mark.anyio
    async def test_range_file_reader_partial_read(self, mock_open, mock_request):
        """Test reading partial chunks at end of range."""
        data = b"0123456789"
        mock_file = MockAsyncFile(data)
        mock_open.return_value.__aenter__ = AsyncMock(return_value=mock_file)
        mock_open.return_value.__aexit__ = AsyncMock(return_value=None)

        chunks = await self.collect_chunks(
            range_file_reader(mock_request, "test.txt", start=0, end=4, chunk_size=10)
        )

        assert len(chunks) == 1
        assert chunks[0] == b"01234"

    @patch("utils.streams.aiofiles.open")
    @pytest.mark.anyio
    async def test_range_file_reader_preserves_filepointer(
        self, mock_open, mock_request, test_data
    ):
        """Test that seek is called with correct position."""
        mock_file = MockAsyncFile(test_data)
        mock_open.return_value.__aenter__ = AsyncMock(return_value=mock_file)
        mock_open.return_value.__aexit__ = AsyncMock(return_value=None)

        await self.collect_chunks(
            range_file_reader(
                mock_request, "test.txt", start=500, end=599, chunk_size=100
            )
        )

        mock_file.seek.assert_called_once_with(500)

    @patch("utils.streams.aiofiles.open")
    @pytest.mark.anyio
    async def test_range_file_reader_filepath_parameter(
        self, mock_open, mock_request, test_data
    ):
        """Test that correct filepath is passed to aiofiles.open."""
        mock_file = MockAsyncFile(test_data)
        mock_open.return_value.__aenter__ = AsyncMock(return_value=mock_file)
        mock_open.return_value.__aexit__ = AsyncMock(return_value=None)

        await self.collect_chunks(
            range_file_reader(
                mock_request, "/path/to/file.mp4", start=0, chunk_size=100
            )
        )

        mock_open.assert_called_once_with("/path/to/file.mp4", "rb")
