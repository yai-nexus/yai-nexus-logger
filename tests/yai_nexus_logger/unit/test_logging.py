"""Unit tests for the yai_nexus_logger configuration and retrieval functions."""

import logging
from unittest.mock import MagicMock

import pytest

from yai_nexus_logger import (
    LoggerConfigurator,
    get_logger,
    init_logging,
)


def clean_logging_environment():
    """A helper to ensure a clean logging state."""
    manager = logging.Manager(logging.root)
    manager.loggerDict.clear()
    logging.root.handlers.clear()
    logging.shutdown()


def test_get_logger_returns_correct_logger(monkeypatch):
    """Test that get_logger returns the correct root or child logger."""
    clean_logging_environment()
    monkeypatch.setenv("LOG_APP_NAME", "my_app")

    root_logger = get_logger()
    child_logger = get_logger("child")

    assert root_logger.name == "my_app"
    assert child_logger.name == "my_app.child"
    assert child_logger.parent is root_logger


def test_init_logging_from_env(monkeypatch):
    """Test init_logging configures the root logger from environment variables."""
    clean_logging_environment()
    monkeypatch.setenv("LOG_APP_NAME", "env_app")
    monkeypatch.setenv("LOG_LEVEL", "DEBUG")
    monkeypatch.setenv("LOG_CONSOLE_ENABLED", "true")
    monkeypatch.setenv("SLS_ENABLED", "false")

    init_logging()

    logger = logging.getLogger("env_app")
    assert logger.level == logging.DEBUG
    assert len(logger.handlers) == 1
    assert isinstance(logger.handlers[0], logging.StreamHandler)


def test_init_logging_with_builder(monkeypatch):
    """Test init_logging configures the root logger using a provided builder."""
    clean_logging_environment()
    monkeypatch.setenv("LOG_APP_NAME", "builder_app")

    builder = LoggerConfigurator(level="WARNING").with_file_handler()
    init_logging(builder)

    logger = logging.getLogger("builder_app")
    assert logger.level == logging.WARNING
    assert len(logger.handlers) == 1
    assert isinstance(logger.handlers[0], logging.handlers.TimedRotatingFileHandler)


def test_init_logging_avoids_reconfiguration(monkeypatch):
    """Test that init_logging does not re-configure an already configured logger."""
    clean_logging_environment()
    monkeypatch.setenv("LOG_APP_NAME", "test_app")

    # Manually configure the logger to simulate it being already configured
    logger = logging.getLogger("test_app")
    logger.addHandler(logging.StreamHandler())

    # Attempt to re-configure, and assert that a warning is raised
    with pytest.warns(UserWarning, match="seems to be already configured"):
        init_logging()


def test_init_logging_sls_missing_vars_warning(monkeypatch):
    """Test that a warning is issued if SLS is enabled but env vars are missing."""
    clean_logging_environment()

    # Manually mock the warning function and SDK availability
    mock_warnings = MagicMock()
    monkeypatch.setattr("yai_nexus_logger.core.warnings", mock_warnings)
    monkeypatch.setattr("yai_nexus_logger.configurator.SLS_SDK_AVAILABLE", True)

    monkeypatch.setenv("LOG_APP_NAME", "sls_test_app")
    monkeypatch.setenv("SLS_ENABLED", "true")
    monkeypatch.delenv("SLS_ENDPOINT", raising=False)

    init_logging()

    mock_warnings.warn.assert_called_once()
    assert (
        "SLS logging is enabled, but some required SLS"
        in mock_warnings.warn.call_args[0][0]
    )


def test_configurator_with_sls_handler_raises_importerror(monkeypatch):
    """Test that LoggerConfigurator.with_sls_handler raises ImportError if SDK is not available."""
    monkeypatch.setattr("yai_nexus_logger.configurator.SLS_SDK_AVAILABLE", False)

    with pytest.raises(ImportError, match="aliyun-log-python-sdk is not installed"):
        LoggerConfigurator().with_sls_handler(
            endpoint="fake-endpoint",
            access_key_id="fake_id",
            access_key_secret="fake_secret",
            project="fake_project",
            logstore="fake_logstore",
        )

