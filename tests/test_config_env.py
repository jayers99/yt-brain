from __future__ import annotations

import os
import tempfile
from pathlib import Path

import pytest
import yaml

from yt_brain.infrastructure.config import YtBrainConfig, load_config, require_api_key
from yt_brain.domain.errors import ConfigError


@pytest.fixture(autouse=True)
def isolated_config_dir(monkeypatch, tmp_path):
    """Each test gets a fresh empty config dir with no pre-existing config file."""
    monkeypatch.setenv("YT_BRAIN_CONFIG_DIR", str(tmp_path))
    monkeypatch.delenv("YOUTUBE_API_KEY", raising=False)
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    return tmp_path


# --- env var tests ---

def test_youtube_api_key_from_env(monkeypatch):
    monkeypatch.setenv("YOUTUBE_API_KEY", "yt-key-from-env")
    config = load_config()
    assert config.youtube_api_key == "yt-key-from-env"


def test_anthropic_api_key_from_env(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "ant-key-from-env")
    config = load_config()
    assert config.anthropic_api_key == "ant-key-from-env"


def test_env_var_overrides_config_file(monkeypatch, isolated_config_dir):
    config_file = isolated_config_dir / "config.yaml"
    config_file.write_text(yaml.dump({"youtube_api_key": "key-from-file"}))

    monkeypatch.setenv("YOUTUBE_API_KEY", "key-from-env")
    config = load_config()
    assert config.youtube_api_key == "key-from-env"


def test_config_file_used_when_no_env(isolated_config_dir):
    config_file = isolated_config_dir / "config.yaml"
    config_file.write_text(yaml.dump({"youtube_api_key": "key-from-file"}))

    config = load_config()
    assert config.youtube_api_key == "key-from-file"


# --- require_api_key tests ---

def test_require_api_key_present():
    config = YtBrainConfig(youtube_api_key="my-key")
    assert require_api_key(config, "youtube_api_key") == "my-key"


def test_require_api_key_missing():
    config = YtBrainConfig()
    with pytest.raises(ConfigError, match="Missing youtube_api_key"):
        require_api_key(config, "youtube_api_key")


def test_require_api_key_missing_anthropic():
    config = YtBrainConfig()
    with pytest.raises(ConfigError, match="Missing anthropic_api_key"):
        require_api_key(config, "anthropic_api_key")


def test_require_api_key_error_message_includes_env_var():
    config = YtBrainConfig()
    with pytest.raises(ConfigError, match="YOUTUBE_API_KEY"):
        require_api_key(config, "youtube_api_key")
