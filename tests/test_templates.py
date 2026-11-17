"""
Tests for URL generation in Jinja templates.

File names containing characters such as ``+`` must be percent-encoded when
interpolated into URLs, otherwise query strings decode ``+`` as a space and
the download route fails with a 500.
"""

from types import SimpleNamespace
from urllib.parse import parse_qsl, urlparse

from fastapi.templating import Jinja2Templates

from core.jinja_filters import register_filters
from files.schemas import FileData

MOANA = (
    "Moana.2026.MULTI.VF2.2160p.WEBRip.MA.DV.HDR10+.x265.EAC3.5.1.Atmos-Amen.mkv"
)


def make_templates() -> Jinja2Templates:
    templates = Jinja2Templates(directory="templates")
    register_filters(templates.env)
    return templates


def extract_query_param(html: str, url_prefix: str, param: str) -> str:
    """Return the decoded value of ``param`` from the first URL starting with ``url_prefix``."""
    for part in html.split('"'):
        if part.startswith(url_prefix):
            query = urlparse(part).query
            return dict(parse_qsl(query))[param]
    raise AssertionError(f"no URL starting with {url_prefix!r} found in template output")


class TestTorrentListTemplate:
    def test_download_link_is_url_encoded(self):
        """The download button must percent-encode the torrent name in file_path."""
        torrent = SimpleNamespace(
            hash_string="abc123",
            name=MOANA,
            status="seeding",
            progress=100,
            peers_sending_to_us=5,
            peers_getting_from_us=2,
            ratio=1.5,
            added_date=1700000000,
            rate_download=0,
            rate_upload=0,
            total_size=4 * 1024**3,
        )
        html = make_templates().get_template("components/torrent_list.html").render(
            torrent_list=[torrent]
        )
        assert f"/files/download?file_path={MOANA.replace('+', '%2B')}" in html
        decoded = extract_query_param(html, "/files/download", "file_path")
        assert decoded == MOANA


class TestFileListTemplate:
    def test_static_link_is_url_encoded(self):
        """The static download link must percent-encode the file name."""
        files = [
            FileData(
                name=MOANA,
                is_dir=False,
                is_archive=False,
                size=4 * 1024**3,
                last_modified=1700000000,
            )
        ]
        html = make_templates().get_template("components/file_list.html").render(
            files=files, folder=None, is_htmx=False
        )
        assert f'href="/static/{MOANA.replace("+", "%2B")}"' in html

    def test_download_and_delete_links_are_url_encoded(self):
        """Directory download/delete links must percent-encode folder and name."""
        files = [
            FileData(
                name="My Folder+1",
                is_dir=True,
                is_archive=False,
                size=None,
                last_modified=1700000000,
            )
        ]
        html = make_templates().get_template("components/file_list.html").render(
            files=files, folder="Parent Dir", is_htmx=False
        )
        encoded = "Parent%20Dir/My%20Folder%2B1"
        assert f"/files/download?file_path={encoded}" in html
        assert f"/files/?file_path={encoded}" in html
        assert f"/files/?folder={encoded}" in html
        assert extract_query_param(html, "/files/download", "file_path") == (
            "Parent Dir/My Folder+1"
        )


class TestZipModalBoxTemplate:
    def test_static_link_is_url_encoded(self):
        """The zip download link must percent-encode the path."""
        html = make_templates().get_template("components/zip_modal_box.html").render(
            path=f"{MOANA}.zip"
        )
        assert f'href="/static/{MOANA.replace("+", "%2B")}.zip"' in html
