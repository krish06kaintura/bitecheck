"""
Sanity tests for BiteCheck Phase 1 Foundation & Tooling.
Verifies configuration loading, path resolution, and logging infrastructure.
"""

from pathlib import Path
from bitecheck.config import settings, BASE_DIR, DATA_DIR
from bitecheck.logger import get_logger


def test_settings_paths():
    """Verify that project base directory and data directory resolve properly."""
    assert isinstance(BASE_DIR, Path)
    assert BASE_DIR.exists()
    assert (BASE_DIR / "requirements.txt").exists()
    assert settings.data_dir == DATA_DIR


def test_settings_defaults():
    """Verify default runtime settings."""
    assert settings.app_env in ["development", "production", "test"]
    assert settings.log_level in ["DEBUG", "INFO", "WARNING", "ERROR"]
    assert settings.port == 8000


def test_logger_initialization():
    """Verify logger creation and message dispatch."""
    logger = get_logger("bitecheck.tests")
    assert logger is not None
    logger.info("Foundation sanity test logging works properly.")
