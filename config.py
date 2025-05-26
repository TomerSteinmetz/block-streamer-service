# config.py
from __future__ import annotations

import os
import pathlib
import yaml
import re
from dataclasses import dataclass, field
from typing import List
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


@dataclass
class ProviderConfig:
    """Static settings for a single provider taken from YAML/env."""

    name: str
    url: str
    timeout_s: float = 8.0
    window_s: int = 60  # sliding window for health metrics

    @classmethod
    def from_dict(cls, data: dict) -> "ProviderConfig":
        """Create ProviderConfig from dictionary with environment variable substitution."""
        # Handle URL template substitution
        if 'url_template' in data:
            url = cls._substitute_env_vars(data['url_template'])
            data = {**data, 'url': url}
            data.pop('url_template', None)
        elif 'url' in data:
            # Also substitute in regular URL field
            data['url'] = cls._substitute_env_vars(data['url'])

        return cls(**data)

    @staticmethod
    def _substitute_env_vars(template: str) -> str:
        """Substitute environment variables in template string."""

        # Replace ${VAR_NAME} with environment variable values
        def replace_var(match):
            var_name = match.group(1)
            value = os.getenv(var_name)
            if value is None:
                raise ValueError(f"Environment variable {var_name} not found")
            return value

        return re.sub(r'\$\{([^}]+)\}', replace_var, template)


@dataclass
class AppConfig:
    chain_id: int = 1
    expected_block_time: int = 12
    poll_interval_s: float = 2.0
    start_confirmations: int = 0
    providers: List[ProviderConfig] = field(default_factory=list)
    lag_threshold_s: int = 30
    failure_ratio: float = 0.2
    score_halflife_s: int = 60

    @classmethod
    def load(cls, path: str | pathlib.Path | None = None) -> "AppConfig":
        """Load configuration from YAML file with environment variable substitution."""
        path = path or os.environ.get("APP_CONFIG", "config.yaml")

        with open(path, "r", encoding="utf-8") as fh:
            raw = yaml.safe_load(fh)

        # Create providers with environment variable substitution
        providers = [ProviderConfig.from_dict(p) for p in raw.pop("providers")]

        # Override other settings from environment variables if available
        config_data = {
            'chain_id': int(os.getenv('CHAIN_ID', raw.get('chain_id', 1))),
            'expected_block_time': int(os.getenv('EXPECTED_BLOCK_TIME', raw.get('expected_block_time', 12))),
            'lag_threshold_s': int(os.getenv('LAG_THRESHOLD_S', raw.get('lag_threshold_s', 30))),
            'failure_ratio': float(os.getenv('FAILURE_RATIO', raw.get('failure_ratio', 0.2))),
            'score_halflife_s': int(os.getenv('SCORE_HALFLIFE_S', raw.get('score_halflife_s', 60))),
            **raw  # Include any other YAML settings
        }

        return cls(providers=providers, **config_data)