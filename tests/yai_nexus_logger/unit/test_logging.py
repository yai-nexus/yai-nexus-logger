"""Unit tests for the yai_nexus_logger configuration and retrieval functions."""

import logging
import os
from unittest.mock import MagicMock, patch

import pytest

from yai_nexus_logger import (
    LoggerConfigurator,
    get_logger,
    init_logging,
    trace_context,
)
from yai_nexus_logger.internal.internal_handlers import SLS_SDK_AVAILABLE


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


@pytest.mark.skipif(not SLS_SDK_AVAILABLE, reason="SLS SDK not installed")
@patch("yai_nexus_logger.internal.internal_handlers.SLSLogHandler.emit")
def test_init_logging_with_sls_handler_mocked(mock_emit, monkeypatch):
    """
    Test that init_logging, when configured for SLS via environment variables,
    correctly adds the SLS handler and that the handler attempts to send logs.
    The handler's emit method is mocked to prevent actual data transmission.
    """
    clean_logging_environment()
    sls_env_vars = {
        "LOG_APP_NAME": "sls_unit_test",
        "LOG_LEVEL": "INFO",
        "SLS_ENABLED": "true",
        "SLS_ENDPOINT": "fake-endpoint.log.aliyuncs.com",
        "SLS_ACCESS_KEY_ID": "fake_id",
        "SLS_ACCESS_KEY_SECRET": "fake_secret",
        "SLS_PROJECT": "fake_project",
        "SLS_LOGSTORE": "fake_logstore",
        "SLS_TOPIC": "test_topic",
    }
    monkeypatch.setattr(os, "environ", sls_env_vars)

    init_logging()
    logger = get_logger("sls_unit_logger")

    trace_id = "trace-for-sls-unit-test"
    trace_context.set_trace_id(trace_id)

    test_message = "This is a unit test message for SLS."
    logger.warning(test_message)

    mock_emit.assert_called_once()
    log_record = mock_emit.call_args[0][0]
    assert test_message in log_record.getMessage()
    assert log_record.levelname == "WARNING"
