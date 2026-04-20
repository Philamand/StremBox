from unittest.mock import patch

import pytest
from fastapi import HTTPException

from utils.streams import check_season_episode, parse_range, resolve_file_path


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
