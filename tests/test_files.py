"""
Tests for the FileManager class.

This file was AI-generated.
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import Request

from files.schemas import FileData
from files.services import ARCHIVE_EXTENSIONS, FileManager


class TestFileManager:
    """Test suite for FileManager class."""

    @pytest.fixture
    def mock_request(self):
        """Create a mock FastAPI request with user transmission data."""
        request = MagicMock(spec=Request)
        request.state.user.transmission_data.download_folder = "/home/user/downloads"
        return request

    @pytest.fixture
    def file_manager(self, mock_request):
        """Create a FileManager instance with mocked request."""
        return FileManager(mock_request)

    # Tests for get_path method
    def test_get_path_without_folder(self, file_manager):
        """Test get_path returns base directory when folder is None."""
        result = file_manager.get_path()
        assert result == "/home/user/downloads"

    def test_get_path_without_folder_explicit_none(self, file_manager):
        """Test get_path returns base directory when folder is explicitly None."""
        result = file_manager.get_path(None)
        assert result == "/home/user/downloads"

    def test_get_path_with_folder(self, file_manager):
        """Test get_path returns joined path when folder is provided."""
        result = file_manager.get_path("subfolder")
        assert result == "/home/user/downloads/subfolder"

    def test_get_path_with_nested_folder(self, file_manager):
        """Test get_path with nested folder paths."""
        result = file_manager.get_path("parent/child/grandchild")
        assert result == "/home/user/downloads/parent/child/grandchild"

    # Tests for is_dir method
    @pytest.mark.asyncio
    async def test_is_dir_true(self, file_manager):
        """Test is_dir returns True for a directory."""
        with patch(
            "files.services.os.path.isdir", new_callable=AsyncMock
        ) as mock_isdir:
            mock_isdir.return_value = True
            result = await file_manager.is_dir("/home/user/downloads/folder")
            assert result is True
            mock_isdir.assert_called_once_with("/home/user/downloads/folder")

    @pytest.mark.asyncio
    async def test_is_dir_false(self, file_manager):
        """Test is_dir returns False for a file."""
        with patch(
            "files.services.os.path.isdir", new_callable=AsyncMock
        ) as mock_isdir:
            mock_isdir.return_value = False
            result = await file_manager.is_dir("/home/user/downloads/file.txt")
            assert result is False
            mock_isdir.assert_called_once_with("/home/user/downloads/file.txt")

    # Tests for exists method
    @pytest.mark.asyncio
    async def test_exists_true(self, file_manager):
        """Test exists returns True when path exists."""
        with patch(
            "files.services.os.path.exists", new_callable=AsyncMock
        ) as mock_exists:
            mock_exists.return_value = True
            result = await file_manager.exists("/home/user/downloads/something")
            assert result is True
            mock_exists.assert_called_once_with("/home/user/downloads/something")

    @pytest.mark.asyncio
    async def test_exists_false(self, file_manager):
        """Test exists returns False when path does not exist."""
        with patch(
            "files.services.os.path.exists", new_callable=AsyncMock
        ) as mock_exists:
            mock_exists.return_value = False
            result = await file_manager.exists("/home/user/downloads/nonexistent")
            assert result is False

    # Tests for list_files method
    @pytest.mark.asyncio
    async def test_list_files_empty_directory(self, file_manager):
        """Test list_files returns empty list for empty directory."""
        with patch("files.services.os.listdir", new_callable=AsyncMock) as mock_listdir:
            mock_listdir.return_value = []
            result = await file_manager.list_files()
            assert result == []
            mock_listdir.assert_called_once_with("/home/user/downloads")

    @pytest.mark.asyncio
    async def test_list_files_with_folder_param(self, file_manager):
        """Test list_files with a specific folder parameter."""
        with patch("files.services.os.listdir", new_callable=AsyncMock) as mock_listdir:
            mock_listdir.return_value = []
            await file_manager.list_files("subfolder")
            mock_listdir.assert_called_once_with("/home/user/downloads/subfolder")

    @pytest.mark.asyncio
    async def test_list_files_mixed_content(self, file_manager):
        """Test list_files with mixed files and directories."""
        with (
            patch("files.services.os.listdir", new_callable=AsyncMock) as mock_listdir,
            patch("files.services.os.path.isdir", new_callable=AsyncMock) as mock_isdir,
            patch(
                "files.services.os.path.getsize", new_callable=AsyncMock
            ) as mock_getsize,
            patch(
                "files.services.os.path.getatime", new_callable=AsyncMock
            ) as mock_getatime,
        ):
            mock_listdir.return_value = ["dir1", "file1.txt", "dir2", "file2.pdf"]

            # Setup mock responses: dir1=True, file1.txt=False, dir2=True, file2.pdf=False
            mock_isdir.side_effect = [True, False, True, False]
            # getsize is only called for files (not directories), so only 2 calls
            mock_getsize.side_effect = [1024, 2048]
            mock_getatime.side_effect = [1000, 1001, 1002, 1003]

            result = await file_manager.list_files()

            assert len(result) == 4
            # Directories should come first, then files, sorted by name
            assert result[0].name == "dir1"
            assert result[0].is_dir is True
            assert result[0].size is None
            assert result[1].name == "dir2"
            assert result[1].is_dir is True
            assert result[2].name == "file1.txt"
            assert result[2].is_dir is False
            assert result[2].size == 1024
            assert result[3].name == "file2.pdf"
            assert result[3].is_dir is False
            assert result[3].size == 2048

    @pytest.mark.asyncio
    async def test_list_files_archive_detection(self, file_manager):
        """Test list_files correctly detects archive files."""
        with (
            patch("files.services.os.listdir", new_callable=AsyncMock) as mock_listdir,
            patch("files.services.os.path.isdir", new_callable=AsyncMock) as mock_isdir,
            patch(
                "files.services.os.path.getsize", new_callable=AsyncMock
            ) as mock_getsize,
            patch(
                "files.services.os.path.getatime", new_callable=AsyncMock
            ) as mock_getatime,
        ):
            mock_listdir.return_value = ["archive.zip", "document.pdf", "backup.tar.gz"]
            mock_isdir.side_effect = [False, False, False]
            mock_getsize.side_effect = [5000, 2000, 3000]
            mock_getatime.side_effect = [1000, 1001, 1002]

            result = await file_manager.list_files()

            assert len(result) == 3
            assert result[0].name == "archive.zip"
            assert result[0].is_archive is True
            assert result[1].name == "backup.tar.gz"
            assert result[1].is_archive is True
            assert result[2].name == "document.pdf"
            assert result[2].is_archive is False

    @pytest.mark.asyncio
    async def test_list_files_case_insensitive_archive_detection(self, file_manager):
        """Test archive detection is case-insensitive."""
        with (
            patch("files.services.os.listdir", new_callable=AsyncMock) as mock_listdir,
            patch("files.services.os.path.isdir", new_callable=AsyncMock) as mock_isdir,
            patch(
                "files.services.os.path.getsize", new_callable=AsyncMock
            ) as mock_getsize,
            patch(
                "files.services.os.path.getatime", new_callable=AsyncMock
            ) as mock_getatime,
        ):
            mock_listdir.return_value = ["ARCHIVE.ZIP", "File.TAR.GZ"]
            mock_isdir.side_effect = [False, False]
            mock_getsize.side_effect = [5000, 3000]
            mock_getatime.side_effect = [1000, 1001]

            result = await file_manager.list_files()

            assert result[0].is_archive is True
            assert result[1].is_archive is True

    @pytest.mark.asyncio
    async def test_list_files_handles_file_not_found(self, file_manager):
        """Test list_files handles FileNotFoundError gracefully."""
        with patch("files.services.os.listdir", new_callable=AsyncMock) as mock_listdir:
            mock_listdir.side_effect = FileNotFoundError()
            result = await file_manager.list_files()
            assert result == []

    @pytest.mark.asyncio
    async def test_list_files_handles_permission_error(self, file_manager):
        """Test list_files handles PermissionError gracefully."""
        with patch("files.services.os.listdir", new_callable=AsyncMock) as mock_listdir:
            mock_listdir.side_effect = PermissionError()
            result = await file_manager.list_files()
            assert result == []

    @pytest.mark.asyncio
    async def test_list_files_skips_inaccessible_items(self, file_manager):
        """Test list_files skips items that raise errors during stat calls."""
        with (
            patch("files.services.os.listdir", new_callable=AsyncMock) as mock_listdir,
            patch("files.services.os.path.isdir", new_callable=AsyncMock) as mock_isdir,
            patch(
                "files.services.os.path.getsize", new_callable=AsyncMock
            ) as mock_getsize,
            patch(
                "files.services.os.path.getatime", new_callable=AsyncMock
            ) as mock_getatime,
        ):
            mock_listdir.return_value = [
                "accessible.txt",
                "inaccessible.txt",
                "another.pdf",
            ]

            # First file accessible, second raises PermissionError, third accessible
            # When isdir raises for inaccessible.txt, that item is skipped
            # So getsize and getatime are only called for accessible items
            mock_isdir.side_effect = [False, PermissionError(), False]
            mock_getsize.side_effect = [1024, 2048]
            mock_getatime.side_effect = [1000, 1002]

            result = await file_manager.list_files()

            assert len(result) == 2
            assert result[0].name == "accessible.txt"
            assert result[1].name == "another.pdf"

    @pytest.mark.asyncio
    async def test_list_files_sorting_directories_first(self, file_manager):
        """Test that list_files sorts directories before files."""
        with (
            patch("files.services.os.listdir", new_callable=AsyncMock) as mock_listdir,
            patch("files.services.os.path.isdir", new_callable=AsyncMock) as mock_isdir,
            patch(
                "files.services.os.path.getsize", new_callable=AsyncMock
            ) as mock_getsize,
            patch(
                "files.services.os.path.getatime", new_callable=AsyncMock
            ) as mock_getatime,
        ):
            # Mix of files and directories with names that would be out of order alphabetically
            mock_listdir.return_value = [
                "zebra.txt",
                "alpha_dir",
                "beta.pdf",
                "charlie_dir",
            ]
            # zebra.txt=False, alpha_dir=True, beta.pdf=False, charlie_dir=True
            mock_isdir.side_effect = [False, True, False, True]
            # getsize only called for files (2 files, indices 0 and 2)
            mock_getsize.side_effect = [100, 200]
            # getatime called for all 4 items
            mock_getatime.side_effect = [1000, 1001, 1002, 1003]

            result = await file_manager.list_files()

            # Directories first (alpha_dir, charlie_dir), then files (beta.pdf, zebra.txt)
            # Within each group, sorted by name (case-insensitive)
            assert result[0].name == "alpha_dir"
            assert result[0].is_dir is True
            assert result[1].name == "charlie_dir"
            assert result[1].is_dir is True
            assert result[2].name == "beta.pdf"
            assert result[2].is_dir is False
            assert result[3].name == "zebra.txt"
            assert result[3].is_dir is False

    @pytest.mark.asyncio
    async def test_list_files_case_insensitive_sorting(self, file_manager):
        """Test that list_files sorts case-insensitively."""
        with (
            patch("files.services.os.listdir", new_callable=AsyncMock) as mock_listdir,
            patch("files.services.os.path.isdir", new_callable=AsyncMock) as mock_isdir,
            patch(
                "files.services.os.path.getsize", new_callable=AsyncMock
            ) as mock_getsize,
            patch(
                "files.services.os.path.getatime", new_callable=AsyncMock
            ) as mock_getatime,
        ):
            mock_listdir.return_value = ["Zebra.txt", "apple.txt", "Banana.txt"]
            mock_isdir.side_effect = [False, False, False]
            mock_getsize.side_effect = [100, 200, 300]
            mock_getatime.side_effect = [1000, 1001, 1002]

            result = await file_manager.list_files()

            # Should be sorted: apple.txt, Banana.txt, Zebra.txt
            assert result[0].name == "apple.txt"
            assert result[1].name == "Banana.txt"
            assert result[2].name == "Zebra.txt"

    # Tests for remove_file method
    @pytest.mark.asyncio
    async def test_remove_file_removes_file(self, file_manager):
        """Test remove_file removes a file successfully."""
        with (
            patch(
                "files.services.os.path.isfile", new_callable=AsyncMock
            ) as mock_isfile,
            patch("files.services.os.remove", new_callable=AsyncMock) as mock_remove,
        ):
            mock_isfile.return_value = True
            await file_manager.remove_file("file.txt")

            mock_isfile.assert_called_once_with("/home/user/downloads/file.txt")
            mock_remove.assert_called_once_with("/home/user/downloads/file.txt")

    @pytest.mark.asyncio
    async def test_remove_file_removes_directory(self, file_manager):
        """Test remove_file removes an empty directory."""
        with (
            patch(
                "files.services.os.path.isfile", new_callable=AsyncMock
            ) as mock_isfile,
            patch("files.services.os.path.isdir", new_callable=AsyncMock) as mock_isdir,
            patch("files.services.os.rmdir", new_callable=AsyncMock) as mock_rmdir,
        ):
            mock_isfile.return_value = False
            mock_isdir.return_value = True
            await file_manager.remove_file("folder")

            mock_isfile.assert_called_once()
            mock_isdir.assert_called_once()
            mock_rmdir.assert_called_once_with("/home/user/downloads/folder")

    @pytest.mark.asyncio
    async def test_remove_file_raises_for_nonexistent_path(self, file_manager):
        """Test remove_file raises FileNotFoundError for nonexistent path."""
        with (
            patch(
                "files.services.os.path.isfile", new_callable=AsyncMock
            ) as mock_isfile,
            patch("files.services.os.path.isdir", new_callable=AsyncMock) as mock_isdir,
        ):
            mock_isfile.return_value = False
            mock_isdir.return_value = False

            with pytest.raises(FileNotFoundError) as exc_info:
                await file_manager.remove_file("nonexistent.txt")

            assert "File not found: /home/user/downloads/nonexistent.txt" in str(
                exc_info.value
            )

    @pytest.mark.asyncio
    async def test_remove_file_with_nested_path(self, file_manager):
        """Test remove_file with nested file paths."""
        with (
            patch(
                "files.services.os.path.isfile", new_callable=AsyncMock
            ) as mock_isfile,
            patch("files.services.os.remove", new_callable=AsyncMock) as mock_remove,
        ):
            mock_isfile.return_value = True
            await file_manager.remove_file("folder/subfolder/file.txt")

            mock_isfile.assert_called_once_with(
                "/home/user/downloads/folder/subfolder/file.txt"
            )
            mock_remove.assert_called_once_with(
                "/home/user/downloads/folder/subfolder/file.txt"
            )

    # Tests for get_folder_size method
    @pytest.mark.asyncio
    async def test_get_folder_size_empty_folder(self, file_manager):
        """Test get_folder_size returns 0 for empty folder."""
        with (
            patch("files.services.os.path.isdir", new_callable=AsyncMock) as mock_isdir,
            patch("files.services._pyos.walk") as mock_walk,
        ):
            mock_isdir.return_value = True
            mock_walk.return_value = [("/home/user/downloads", [], [])]

            result = await file_manager.get_folder_size()
            assert result == 0

    @pytest.mark.asyncio
    async def test_get_folder_size_single_file(self, file_manager):
        """Test get_folder_size with a single file."""
        with (
            patch("files.services.os.path.isdir", new_callable=AsyncMock) as mock_isdir,
            patch("files.services._pyos.walk") as mock_walk,
            patch(
                "files.services.os.path.getsize", new_callable=AsyncMock
            ) as mock_getsize,
        ):
            mock_isdir.return_value = True
            mock_walk.return_value = [("/home/user/downloads", [], ["file.txt"])]
            mock_getsize.return_value = 1024

            result = await file_manager.get_folder_size()
            assert result == 1024

    @pytest.mark.asyncio
    async def test_get_folder_size_multiple_files(self, file_manager):
        """Test get_folder_size with multiple files."""
        with (
            patch("files.services.os.path.isdir", new_callable=AsyncMock) as mock_isdir,
            patch("files.services._pyos.walk") as mock_walk,
            patch(
                "files.services.os.path.getsize", new_callable=AsyncMock
            ) as mock_getsize,
        ):
            mock_isdir.return_value = True
            mock_walk.return_value = [
                ("/home/user/downloads", [], ["file1.txt", "file2.pdf"])
            ]
            mock_getsize.side_effect = [1024, 2048]

            result = await file_manager.get_folder_size()
            assert result == 3072

    @pytest.mark.asyncio
    async def test_get_folder_size_recursive(self, file_manager):
        """Test get_folder_size recursively sums files in subdirectories."""
        with (
            patch("files.services.os.path.isdir", new_callable=AsyncMock) as mock_isdir,
            patch("files.services._pyos.walk") as mock_walk,
            patch(
                "files.services.os.path.getsize", new_callable=AsyncMock
            ) as mock_getsize,
        ):
            mock_isdir.return_value = True
            mock_walk.return_value = [
                ("/home/user/downloads", ["subdir"], ["file1.txt"]),
                ("/home/user/downloads/subdir", [], ["file2.pdf", "file3.zip"]),
            ]
            mock_getsize.side_effect = [1000, 2000, 3000]

            result = await file_manager.get_folder_size()
            assert result == 6000

    @pytest.mark.asyncio
    async def test_get_folder_size_with_folder_param(self, file_manager):
        """Test get_folder_size with specific folder parameter."""
        with (
            patch("files.services.os.path.isdir", new_callable=AsyncMock) as mock_isdir,
            patch("files.services._pyos.walk") as mock_walk,
            patch(
                "files.services.os.path.getsize", new_callable=AsyncMock
            ) as mock_getsize,
        ):
            mock_isdir.return_value = True
            mock_walk.return_value = [
                ("/home/user/downloads/subfolder", [], ["file.txt"])
            ]
            mock_getsize.return_value = 1024

            result = await file_manager.get_folder_size("subfolder")
            assert result == 1024
            mock_isdir.assert_called_once_with("/home/user/downloads/subfolder")

    @pytest.mark.asyncio
    async def test_get_folder_size_nonexistent_folder(self, file_manager):
        """Test get_folder_size returns 0 for nonexistent folder."""
        with patch(
            "files.services.os.path.isdir", new_callable=AsyncMock
        ) as mock_isdir:
            mock_isdir.side_effect = FileNotFoundError()
            result = await file_manager.get_folder_size()
            assert result == 0

    @pytest.mark.asyncio
    async def test_get_folder_size_permission_denied(self, file_manager):
        """Test get_folder_size returns 0 when permission denied."""
        with patch(
            "files.services.os.path.isdir", new_callable=AsyncMock
        ) as mock_isdir:
            mock_isdir.side_effect = PermissionError()
            result = await file_manager.get_folder_size()
            assert result == 0

    @pytest.mark.asyncio
    async def test_get_folder_size_not_a_directory(self, file_manager):
        """Test get_folder_size returns 0 when path is not a directory."""
        with patch(
            "files.services.os.path.isdir", new_callable=AsyncMock
        ) as mock_isdir:
            mock_isdir.return_value = False
            result = await file_manager.get_folder_size()
            assert result == 0

    @pytest.mark.asyncio
    async def test_get_folder_size_skips_inaccessible_files(self, file_manager):
        """Test get_folder_size skips files that raise errors."""
        with (
            patch("files.services.os.path.isdir", new_callable=AsyncMock) as mock_isdir,
            patch("files.services._pyos.walk") as mock_walk,
            patch(
                "files.services.os.path.getsize", new_callable=AsyncMock
            ) as mock_getsize,
        ):
            mock_isdir.return_value = True
            mock_walk.return_value = [
                (
                    "/home/user/downloads",
                    [],
                    ["accessible.txt", "inaccessible.txt", "another.pdf"],
                )
            ]
            # First file accessible, second raises error, third accessible
            mock_getsize.side_effect = [1000, PermissionError(), 2000]

            result = await file_manager.get_folder_size()
            assert result == 3000

    @pytest.mark.asyncio
    async def test_get_folder_size_handles_walk_errors(self, file_manager):
        """Test get_folder_size handles errors during walk."""
        with (
            patch("files.services.os.path.isdir", new_callable=AsyncMock) as mock_isdir,
            patch("files.services._pyos.walk") as mock_walk,
        ):
            mock_isdir.return_value = True
            mock_walk.side_effect = PermissionError()

            result = await file_manager.get_folder_size()
            assert result == 0


class TestFileDataSchema:
    """Test suite for FileData schema."""

    def test_file_data_file(self):
        """Test FileData for a regular file."""
        file_data = FileData(
            name="document.pdf",
            is_dir=False,
            is_archive=False,
            size=2048,
            last_modified=1234567890,
        )
        assert file_data.name == "document.pdf"
        assert file_data.is_dir is False
        assert file_data.is_archive is False
        assert file_data.size == 2048
        assert file_data.last_modified == 1234567890

    def test_file_data_directory(self):
        """Test FileData for a directory."""
        file_data = FileData(
            name="my_folder", is_dir=True, is_archive=False, last_modified=1234567890
        )
        assert file_data.name == "my_folder"
        assert file_data.is_dir is True
        assert file_data.is_archive is False
        assert file_data.size is None
        assert file_data.last_modified == 1234567890

    def test_file_data_archive(self):
        """Test FileData for an archive file."""
        file_data = FileData(
            name="backup.zip",
            is_dir=False,
            is_archive=True,
            size=5000,
            last_modified=1234567890,
        )
        assert file_data.is_archive is True
        assert file_data.size == 5000


class TestArchiveExtensions:
    """Test suite for archive extensions constant."""

    def test_archive_extensions_contains_common_formats(self):
        """Test that ARCHIVE_EXTENSIONS contains common archive formats."""
        assert ".zip" in ARCHIVE_EXTENSIONS
        assert ".rar" in ARCHIVE_EXTENSIONS
        assert ".tar.gz" in ARCHIVE_EXTENSIONS
        assert ".7z" in ARCHIVE_EXTENSIONS
        assert ".gz" in ARCHIVE_EXTENSIONS

    def test_archive_extensions_is_tuple(self):
        """Test that ARCHIVE_EXTENSIONS is a tuple."""
        assert isinstance(ARCHIVE_EXTENSIONS, tuple)

    def test_archive_extensions_non_empty(self):
        """Test that ARCHIVE_EXTENSIONS is not empty."""
        assert len(ARCHIVE_EXTENSIONS) > 0
