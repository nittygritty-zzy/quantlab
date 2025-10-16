"""
Configuration management for QuantLab
"""

import os
import yaml
from pathlib import Path
from dataclasses import dataclass
from typing import Optional


@dataclass
class Config:
    """Configuration data class"""
    # API Keys
    polygon_api_key: str
    alphavantage_api_key: str

    # Database
    database_path: str

    # Data paths
    parquet_root: str
    qlib_root: Optional[str] = None

    # Cache settings
    cache_ttl_prices: int = 900  # 15 minutes
    cache_ttl_fundamentals: int = 86400  # 24 hours
    cache_ttl_news: int = 3600  # 1 hour

    # Rate limits (requests per minute)
    polygon_rate_limit: int = 5  # Starter plan
    alphavantage_rate_limit: int = 5  # Free tier


def load_config(config_path: Optional[str] = None) -> Config:
    """
    Load configuration from file or environment variables

    Priority:
    1. Specified config_path
    2. ~/.quantlab/config.yaml
    3. Environment variables
    """
    if config_path is None:
        config_path = os.path.expanduser("~/.quantlab/config.yaml")

    # Default values from environment or hardcoded
    config_data = {
        "polygon_api_key": os.getenv("POLYGON_API_KEY", "vDr8GDaQ87Z9Mwe5IiCKzGcRP9pnO8TW"),
        "alphavantage_api_key": os.getenv("ALPHAVANTAGE_API_KEY", "3NHDCBRE0IKFB8XW"),
        "database_path": os.path.expanduser("~/.quantlab/quantlab.duckdb"),
        "parquet_root": "/Volumes/sandisk/quantmini-data/data/parquet",
        "qlib_root": "/Volumes/sandisk/quantmini-data/data/qlib",
    }

    # Load from YAML if exists
    if os.path.exists(config_path):
        with open(config_path, 'r') as f:
            yaml_config = yaml.safe_load(f) or {}

        # Merge YAML config
        if "api_keys" in yaml_config:
            config_data["polygon_api_key"] = yaml_config["api_keys"].get("polygon", config_data["polygon_api_key"])
            config_data["alphavantage_api_key"] = yaml_config["api_keys"].get("alphavantage", config_data["alphavantage_api_key"])

        if "database" in yaml_config:
            config_data["database_path"] = os.path.expanduser(yaml_config["database"].get("path", config_data["database_path"]))

        if "data_paths" in yaml_config:
            config_data["parquet_root"] = yaml_config["data_paths"].get("parquet_root", config_data["parquet_root"])
            config_data["qlib_root"] = yaml_config["data_paths"].get("qlib_root", config_data["qlib_root"])

        if "cache" in yaml_config:
            config_data.update(yaml_config["cache"])

        if "rate_limits" in yaml_config:
            config_data["polygon_rate_limit"] = yaml_config["rate_limits"].get("polygon", 5)
            config_data["alphavantage_rate_limit"] = yaml_config["rate_limits"].get("alphavantage", 5)

    return Config(**config_data)


def create_default_config(config_path: Optional[str] = None) -> None:
    """Create a default configuration file"""
    if config_path is None:
        config_path = os.path.expanduser("~/.quantlab/config.yaml")

    config_dir = os.path.dirname(config_path)
    os.makedirs(config_dir, exist_ok=True)

    default_config = {
        "api_keys": {
            "polygon": "your_polygon_api_key_here",
            "alphavantage": "your_alphavantage_api_key_here",
        },
        "database": {
            "path": "~/.quantlab/quantlab.duckdb"
        },
        "data_paths": {
            "parquet_root": "/Volumes/sandisk/quantmini-data/data/parquet",
            "qlib_root": "/Volumes/sandisk/quantmini-data/data/qlib"
        },
        "cache": {
            "cache_ttl_prices": 900,
            "cache_ttl_fundamentals": 86400,
            "cache_ttl_news": 3600
        },
        "rate_limits": {
            "polygon": 5,
            "alphavantage": 5
        }
    }

    with open(config_path, 'w') as f:
        yaml.dump(default_config, f, default_flow_style=False, sort_keys=False)

    print(f"✓ Created default config at: {config_path}")
