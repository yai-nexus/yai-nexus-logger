"""Unit tests for the Uvicorn support module."""
import pytest
from yai_nexus_logger.uvicorn_support import get_default_uvicorn_log_config


def test_get_default_uvicorn_log_config_returns_dict():
    """Test that the function returns a dictionary."""
    config = get_default_uvicorn_log_config()
    assert isinstance(config, dict)


def test_get_default_uvicorn_log_config_top_level_keys():
    """Test that the dictionary contains the expected top-level keys."""
    config = get_default_uvicorn_log_config()
    expected_keys = [
        "version",
        "disable_existing_loggers",
        "formatters",
        "handlers",
        "loggers",
    ]
    for key in expected_keys:
        assert key in config


@pytest.mark.parametrize("level", ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"])
def test_get_default_uvicorn_log_config_level(level):
    """Test that the log level is correctly set for all loggers."""
    config = get_default_uvicorn_log_config(level=level)
    assert config["loggers"]["uvicorn"]["level"] == level
    assert config["loggers"]["uvicorn.error"]["level"] == level
    assert config["loggers"]["uvicorn.access"]["level"] == level


def test_get_default_uvicorn_log_config_level_case_insensitivity():
    """Test that the log level is correctly capitalized."""
    config = get_default_uvicorn_log_config(level="debug")
    assert config["loggers"]["uvicorn"]["level"] == "DEBUG"
    assert config["loggers"]["uvicorn.error"]["level"] == "DEBUG"
    assert config["loggers"]["uvicorn.access"]["level"] == "DEBUG"


def test_get_default_uvicorn_log_config_default_level():
    """Test that the default log level is INFO."""
    config = get_default_uvicorn_log_config()
    assert config["loggers"]["uvicorn"]["level"] == "INFO"
    assert config["loggers"]["uvicorn.error"]["level"] == "INFO"
    assert config["loggers"]["uvicorn.access"]["level"] == "INFO" 