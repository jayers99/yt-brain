import os
import tempfile
from collections.abc import Generator
from pathlib import Path

import pytest


@pytest.fixture(autouse=True)
def _clear_api_keys(monkeypatch):
    """Ensure no real API keys leak into tests."""
    monkeypatch.delenv("YOUTUBE_API_KEY", raising=False)
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)


@pytest.fixture
def temp_config_dir() -> Generator[Path, None, None]:
    with tempfile.TemporaryDirectory() as tmpdir:
        path = Path(tmpdir)
        old_env = os.environ.get("YT_BRAIN_CONFIG_DIR")
        os.environ["YT_BRAIN_CONFIG_DIR"] = str(path)
        try:
            yield path
        finally:
            if old_env is None:
                os.environ.pop("YT_BRAIN_CONFIG_DIR", None)
            else:
                os.environ["YT_BRAIN_CONFIG_DIR"] = old_env


@pytest.fixture
def temp_db(temp_config_dir: Path) -> Path:
    from yt_brain.infrastructure.database import init_db

    db_path = temp_config_dir / "yt-brain.db"
    init_db(db_path)
    return db_path
