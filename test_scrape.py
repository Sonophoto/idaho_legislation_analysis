"""
Tests for scrape.py — verifies uv setup and scraping logic.

Run with::

    uv run pytest test_scrape.py -v
"""

import os
import tempfile

import responses
import pytest

from scrape import (
    BASE_URL,
    LEGISLATION_URL,
    scrape_idaho_legislation,
    parse_detail_page,
    download_pdf,
    main,
)

# ---------------------------------------------------------------------------
# Dependency / uv-setup smoke tests
# ---------------------------------------------------------------------------


class TestUvSetup:
    """Verify that uv installed all required dependencies correctly."""

    def test_import_beautifulsoup4(self):
        from bs4 import BeautifulSoup  # noqa: F401

    def test_import_pandas(self):
        import pandas  # noqa: F401

    def test_import_requests(self):
        import requests  # noqa: F401

    def test_import_tenacity(self):
        import tenacity  # noqa: F401

    def test_import_ratelimit(self):
        import ratelimit  # noqa: F401

    def test_import_mammoth(self):
        import mammoth  # noqa: F401

    def test_import_openai(self):
        import openai  # noqa: F401

    def test_import_streamlit(self):
        import streamlit  # noqa: F401

    def test_import_plotly(self):
        import plotly  # noqa: F401


# ---------------------------------------------------------------------------
# HTML fixtures — minimal pages that match what the Idaho Legislature serves
# ---------------------------------------------------------------------------

INDEX_HTML = """\
<html>
<body>
<!-- first two mini-data-tables are skipped by scrape.py -->
<table class="mini-data-table"><tr><td>skip</td></tr></table>
<table class="mini-data-table"><tr><td>skip</td></tr></table>

<!-- real bill table -->
<table class="mini-data-table">
  <tr id="billH0001">
    <td><a href="/sessioninfo/2026/legislation/H0001">H0001</a></td>
    <td>Test Bill Title</td>
    <td>01/15/2026</td>
    <td>Introduced</td>
  </tr>
</table>

<table class="mini-data-table">
  <tr id="billS1001">
    <td><a href="/sessioninfo/2026/legislation/S1001">S1001</a></td>
    <td>Another Bill</td>
    <td>01/20/2026</td>
    <td>Passed</td>
  </tr>
</table>
</body>
</html>
"""

DETAIL_HTML = """\
<html>
<body>
<table class="bill-table">
  <tr>
    <td>H0001</td>
    <td>Test Bill Title</td>
    <td>by Rep. Smith</td>
  </tr>
</table>
</body>
</html>
"""

FAKE_PDF_CONTENT = b"%PDF-1.4 fake pdf content for testing"


# ---------------------------------------------------------------------------
# Scraping logic tests (mocked HTTP)
# ---------------------------------------------------------------------------


class TestScrapeIdahoLegislation:
    """Test the index-page parser with mocked HTTP."""

    @responses.activate
    def test_parses_bills_from_index_page(self):
        responses.add(
            responses.GET,
            LEGISLATION_URL,
            body=INDEX_HTML,
            status=200,
        )

        import requests as req

        session = req.Session()
        results = scrape_idaho_legislation(session, LEGISLATION_URL)
        session.close()

        assert len(results) == 2

        # First bill
        assert results[0][0] == "H0001"
        assert results[0][1] == "Test Bill Title"
        assert results[0][2] == "Introduced"
        assert results[0][3] == "/sessioninfo/2026/legislation/H0001"
        assert "H0001.pdf" in results[0][4]

        # Second bill
        assert results[1][0] == "S1001"
        assert results[1][1] == "Another Bill"
        assert results[1][2] == "Passed"

    @responses.activate
    def test_skips_tables_without_bill_rows(self):
        html = """\
        <html><body>
        <table class="mini-data-table"><tr><td>skip</td></tr></table>
        <table class="mini-data-table"><tr><td>skip</td></tr></table>
        <table class="mini-data-table">
          <tr><td>no bill id prefix</td></tr>
        </table>
        </body></html>
        """
        responses.add(responses.GET, LEGISLATION_URL, body=html, status=200)

        import requests as req

        session = req.Session()
        results = scrape_idaho_legislation(session, LEGISLATION_URL)
        session.close()

        assert results == []


class TestParseDetailPage:
    """Test the detail-page sponsor parser with mocked HTTP."""

    @responses.activate
    def test_extracts_sponsor(self):
        detail_path = "/sessioninfo/2026/legislation/H0001"
        responses.add(
            responses.GET,
            BASE_URL + detail_path,
            body=DETAIL_HTML,
            status=200,
        )

        import requests as req

        session = req.Session()
        sponsor = parse_detail_page(session, detail_path)
        session.close()

        assert sponsor == "Rep. Smith"

    @responses.activate
    def test_strips_by_prefix(self):
        html = """\
        <html><body>
        <table class="bill-table">
          <tr><td>S1001</td><td>Title</td><td>by   Sen. Jones  </td></tr>
        </table>
        </body></html>
        """
        responses.add(
            responses.GET,
            BASE_URL + "/sessioninfo/2026/legislation/S1001",
            body=html,
            status=200,
        )

        import requests as req

        session = req.Session()
        sponsor = parse_detail_page(session, "/sessioninfo/2026/legislation/S1001")
        session.close()

        assert sponsor == "Sen. Jones"


class TestDownloadPdf:
    """Test PDF download with mocked HTTP."""

    @responses.activate
    def test_downloads_pdf_to_directory(self):
        pdf_url = f"{BASE_URL}/wp-content/uploads/sessioninfo/2026/legislation/H0001.pdf"
        responses.add(responses.GET, pdf_url, body=FAKE_PDF_CONTENT, status=200)

        import requests as req

        with tempfile.TemporaryDirectory() as tmpdir:
            session = req.Session()
            path = download_pdf(session, pdf_url, tmpdir)
            session.close()

            assert os.path.isfile(path)
            assert path.endswith("H0001.pdf")
            with open(path, "rb") as f:
                assert f.read() == FAKE_PDF_CONTENT


# ---------------------------------------------------------------------------
# Full pipeline integration test (mocked HTTP)
# ---------------------------------------------------------------------------


class TestMainPipeline:
    """Test the full scrape pipeline end-to-end with mocked HTTP."""

    @responses.activate
    def test_main_creates_csv_and_datarun(self):
        # Mock index page
        responses.add(responses.GET, LEGISLATION_URL, body=INDEX_HTML, status=200)

        # Mock detail pages for both bills
        responses.add(
            responses.GET,
            BASE_URL + "/sessioninfo/2026/legislation/H0001",
            body=DETAIL_HTML,
            status=200,
        )
        detail_html_s1001 = """\
        <html><body>
        <table class="bill-table">
          <tr><td>S1001</td><td>Another Bill</td><td>by Sen. Jones</td></tr>
        </table>
        </body></html>
        """
        responses.add(
            responses.GET,
            BASE_URL + "/sessioninfo/2026/legislation/S1001",
            body=detail_html_s1001,
            status=200,
        )

        # Mock PDF downloads
        responses.add(
            responses.GET,
            f"{BASE_URL}/wp-content/uploads/sessioninfo/2026/legislation/H0001.pdf",
            body=FAKE_PDF_CONTENT,
            status=200,
        )
        responses.add(
            responses.GET,
            f"{BASE_URL}/wp-content/uploads/sessioninfo/2026/legislation/S1001.pdf",
            body=FAKE_PDF_CONTENT,
            status=200,
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            data_dir = os.path.join(tmpdir, "Data")
            os.makedirs(data_dir, exist_ok=True)

            # Patch working directory and DATARUN
            orig_cwd = os.getcwd()
            os.chdir(tmpdir)
            os.environ["DATARUN"] = "01_01_2026"
            try:
                main()

                # Check datarun file was written
                datarun_file = os.path.join(data_dir, ".datarun")
                assert os.path.isfile(datarun_file)
                with open(datarun_file) as f:
                    assert f.read().strip() == "01_01_2026"

                # Check CSV was created with expected data
                csv_path = os.path.join(data_dir, "01_01_2026", "idaho_bills_01_01_2026.csv")
                assert os.path.isfile(csv_path)

                import pandas as pd

                df = pd.read_csv(csv_path)
                assert len(df) == 2
                assert list(df.columns) == [
                    "bill_number",
                    "bill_title",
                    "bill_status",
                    "detail_link",
                    "pdf_url",
                    "sponsor",
                    "local_pdf_path",
                ]
                assert df.iloc[0]["bill_number"] == "H0001"
                assert df.iloc[0]["sponsor"] == "Rep. Smith"
                assert df.iloc[1]["bill_number"] == "S1001"
                assert df.iloc[1]["sponsor"] == "Sen. Jones"

                # Check PDFs were downloaded
                pdf_dir = os.path.join(data_dir, "01_01_2026")
                assert os.path.isfile(os.path.join(pdf_dir, "H0001.pdf"))
                assert os.path.isfile(os.path.join(pdf_dir, "S1001.pdf"))
            finally:
                os.chdir(orig_cwd)
                os.environ.pop("DATARUN", None)
