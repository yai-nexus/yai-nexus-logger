"""Unit tests for the internal log handlers."""

import logging
import sys
from unittest.mock import MagicMock, patch

import pytest

from yai_nexus_logger.internal.internal_handlers import (
    get_console_handler,
    get_file_handler,
)


@pytest.fixture
def mock_formatter():
    """Fixture to create a mock logging formatter."""
    return MagicMock(spec=logging.Formatter)


def test_get_console_handler(mock_formatter):
    """Test the get_console_handler function."""
    handler = get_console_handler(mock_formatter)

    assert isinstance(handler, logging.StreamHandler)
    assert handler.formatter == mock_formatter
    assert handler.stream == sys.stdout


@patch("pathlib.Path.mkdir")
def test_get_file_handler(mock_mkdir, mock_formatter, tmp_path):
    """Test the get_file_handler function."""
    log_file = tmp_path / "app.log"
    handler = get_file_handler(
        formatter=mock_formatter,
        path=str(log_file),
        when="midnight",
        interval=1,
        backup_count=30,
    )

    assert isinstance(handler, logging.handlers.TimedRotatingFileHandler)
    assert handler.formatter == mock_formatter
    mock_mkdir.assert_called_once_with(parents=True, exist_ok=True)
    assert handler.baseFilename == str(log_file)
    assert handler.when == "MIDNIGHT"
    assert handler.backupCount == 30
    assert handler.encoding == "utf-8"


def test_get_file_handler_creates_directory(mock_formatter, tmp_path):
    """
    Test that get_file_handler creates the log directory if it doesn't exist.
    """
    log_dir = tmp_path / "test_logs"
    log_file = log_dir / "app.log"

    assert not log_dir.exists()

    get_file_handler(formatter=mock_formatter, path=str(log_file))

    assert log_dir.exists()
