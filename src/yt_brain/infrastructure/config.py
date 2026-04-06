from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

import yaml

DEFAULT_CONFIG_DIR = Path.home() / ".config" / "yt-brain"
CONFIG_DIR_ENV = "YT_BRAIN_CONFIG_DIR"


@dataclass
class YtBrainConfig:
    config_dir: Path = field(default_factory=lambda: DEFAULT_CONFIG_DIR)
    youtube_api_key: str = ""
    anthropic_api_key: str = ""
    bounce_threshold: float = 0.15
    watched_threshold: float = 0.85
    transcript_language: str = "en"

    @property
    def db_path(self) -> Path:
        return self.config_dir / "yt-brain.db"

    @property
    def config_file(self) -> Path:
        return self.config_dir / "config.yaml"


def get_config_dir() -> Path:
    env_val = os.environ.get(CONFIG_DIR_ENV)
    if env_val:
        return Path(env_val)
    return DEFAULT_CONFIG_DIR


def load_config() -> YtBrainConfig:
    config_dir = get_config_dir()
    config_file = config_dir / "config.yaml"

    config = YtBrainConfig(config_dir=config_dir)

    if config_file.exists():
        with open(config_file) as f:
            data = yaml.safe_load(f) or {}

        if "youtube_api_key" in data:
            config.youtube_api_key = data["youtube_api_key"]
        if "anthropic_api_key" in data:
            config.anthropic_api_key = data["anthropic_api_key"]
        if "thresholds" in data:
            thresholds = data["thresholds"]
            if "bounced_below" in thresholds:
                config.bounce_threshold = float(thresholds["bounced_below"])
            if "watched_above" in thresholds:
                config.watched_threshold = float(thresholds["watched_above"])
        if "transcript_language" in data:
            config.transcript_language = data["transcript_language"]

    # Environment variables override config file
    env_yt = os.environ.get("YOUTUBE_API_KEY")
    if env_yt:
        config.youtube_api_key = env_yt
    env_ant = os.environ.get("ANTHROPIC_API_KEY")
    if env_ant:
        config.anthropic_api_key = env_ant

    return config


def require_api_key(config: YtBrainConfig, key_name: str) -> str:
    """Get a required API key or raise ConfigError with setup instructions."""
    from yt_brain.domain.errors import ConfigError

    value = getattr(config, key_name, "")
    if not value:
        env_var = {
            "youtube_api_key": "YOUTUBE_API_KEY",
            "anthropic_api_key": "ANTHROPIC_API_KEY",
        }.get(key_name, key_name.upper())

        raise ConfigError(
            f"Missing {key_name}. Set it via:\n"
            f"  1. Environment variable: export {env_var}=<your-key>\n"
            f"  2. Config file: {config.config_file}"
        )
    return value


def save_config(config: YtBrainConfig) -> None:
    config.config_dir.mkdir(parents=True, exist_ok=True)
    data = {
        "youtube_api_key": config.youtube_api_key,
        "anthropic_api_key": config.anthropic_api_key,
        "thresholds": {
            "bounced_below": config.bounce_threshold,
            "watched_above": config.watched_threshold,
        },
        "transcript_language": config.transcript_language,
    }
    with open(config.config_file, "w") as f:
        yaml.dump(data, f, default_flow_style=False, sort_keys=False)
