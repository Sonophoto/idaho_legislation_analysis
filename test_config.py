"""
Tests for config.py — DATARUN resolution logic.

Run with::

    uv run pytest test_config.py -v
"""

import os
import tempfile

import pytest

from config import get_datarun, save_datarun, _detect_datarun_from_files


class TestSaveDatarun:
    """Test persisting the datarun value."""

    def test_writes_datarun_file(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = os.path.join(tmpdir, "Data", ".datarun")
            # Temporarily patch the module-level constant
            import config

            orig = config.DATARUN_FILE
            config.DATARUN_FILE = path
            try:
                save_datarun("02_08_2026")
                assert os.path.isfile(path)
                with open(path) as f:
                    assert f.read().strip() == "02_08_2026"
            finally:
                config.DATARUN_FILE = orig


class TestGetDatarun:
    """Test the DATARUN resolution priority."""

    def test_env_var_takes_priority(self):
        os.environ["DATARUN"] = "12_25_2025"
        try:
            assert get_datarun() == "12_25_2025"
        finally:
            os.environ.pop("DATARUN", None)

    def test_reads_from_datarun_file(self):
        import config

        os.environ.pop("DATARUN", None)
        with tempfile.TemporaryDirectory() as tmpdir:
            path = os.path.join(tmpdir, ".datarun")
            with open(path, "w") as f:
                f.write("03_15_2026\n")
            orig = config.DATARUN_FILE
            config.DATARUN_FILE = path
            try:
                assert get_datarun() == "03_15_2026"
            finally:
                config.DATARUN_FILE = orig

    def test_exits_when_no_datarun_available(self):
        import config

        os.environ.pop("DATARUN", None)
        orig_file = config.DATARUN_FILE
        orig_pattern = config._ENRICHED_PATTERN
        config.DATARUN_FILE = "/nonexistent/.datarun"
        config._ENRICHED_PATTERN = "/nonexistent/*.jsonl"
        try:
            with pytest.raises(SystemExit):
                get_datarun()
        finally:
            config.DATARUN_FILE = orig_file
            config._ENRICHED_PATTERN = orig_pattern


class TestDetectDatarunFromFiles:
    """Test auto-detection of DATARUN from enriched JSONL files."""

    def test_detects_latest_datarun(self):
        import config

        with tempfile.TemporaryDirectory() as tmpdir:
            # Create fake enriched files
            for name in [
                "idaho_bills_enriched_01_15_2026.jsonl",
                "idaho_bills_enriched_04_30_2025.jsonl",
                "idaho_bills_enriched_12_01_2025.jsonl",
            ]:
                with open(os.path.join(tmpdir, name), "w") as f:
                    f.write("{}\n")

            orig = config._ENRICHED_PATTERN
            orig_re = config._ENRICHED_RE
            config._ENRICHED_PATTERN = os.path.join(tmpdir, "idaho_bills_enriched_*.jsonl")
            try:
                result = _detect_datarun_from_files()
                assert result == "01_15_2026"
            finally:
                config._ENRICHED_PATTERN = orig

    def test_returns_none_when_no_files(self):
        import config

        orig = config._ENRICHED_PATTERN
        config._ENRICHED_PATTERN = "/nonexistent/idaho_bills_enriched_*.jsonl"
        try:
            assert _detect_datarun_from_files() is None
        finally:
            config._ENRICHED_PATTERN = orig
