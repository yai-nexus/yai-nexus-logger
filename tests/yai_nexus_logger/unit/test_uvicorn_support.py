"""Unit tests for the yai_nexus_logger.uvicorn_support module."""

import logging
from unittest.mock import MagicMock, patch

import pytest

from yai_nexus_logger.trace_context import trace_context
from yai_nexus_logger.uvicorn_support import (
    UvicornAccessFormatter,
    configure_uvicorn_logging,
)


@pytest.fixture
def mock_record():
    """Fixture to create a mock logging record."""
    record = logging.LogRecord(
        name="uvicorn.access",
        level=logging.INFO,
        pathname="/test",
        lineno=1,
        msg="%s %s %s %s %s",
        args=(
            "127.0.0.1:12345",
            "GET",
            "/test",
            "HTTP/1.1",
            200,
        ),
        exc_info=None,
    )
    # Add attributes that AccessFormatter expects
    record.client_addr = "127.0.0.1:12345"
    record.request_line = "GET /test HTTP/1.1"
    record.status_code = 200
    return record


def test_uvicorn_access_formatter_with_trace_id(mock_record):
    """
    Test that UvicornAccessFormatter includes the trace_id in the log.
    """
    trace_id = "test-trace-id-123"
    token = trace_context.set_trace_id(trace_id)

    formatter = UvicornAccessFormatter()
    formatted_message = formatter.format(mock_record)

    assert f"[{trace_id}]" in formatted_message
    assert "127.0.0.1:12345" in formatted_message
    assert "GET /test HTTP/1.1" in formatted_message
    assert "200" in formatted_message

    trace_context.reset_trace_id(token)


def test_uvicorn_access_formatter_without_trace_id(mock_record):
    """
    Test that UvicornAccessFormatter handles cases where no trace_id is set.
    """
    # Ensure trace_id is not set
    trace_context.set_trace_id(None)

    formatter = UvicornAccessFormatter()
    formatted_message = formatter.format(mock_record)

    assert "[No-Trace-ID]" in formatted_message
    assert "127.0.0.1:12345" in formatted_message
    assert "GET /test HTTP/1.1" in formatted_message
    assert "200" in formatted_message


@patch("logging.getLogger")
def test_configure_uvicorn_logging(mock_getLogger):
    """
    Test that configure_uvicorn_logging correctly configures only uvicorn.access logger.
    """
    # Arrange
    mock_uvicorn_access = MagicMock()

    def getitem(name):
        if name == "uvicorn.access":
            return mock_uvicorn_access
        return MagicMock()

    mock_getLogger.side_effect = getitem

    mock_handler1 = logging.StreamHandler()
    mock_handler2 = logging.FileHandler("test.log")
    handlers = [mock_handler1, mock_handler2]
    level = "DEBUG"

    # Act
    configure_uvicorn_logging(handlers=handlers, level=level)

    # Assert
    # Check that only uvicorn.access handler was cleared and configured
    mock_uvicorn_access.handlers.clear.assert_called_once()
    # Both StreamHandler and FileHandler should be copied (2 handlers), as both have stream attribute
    assert mock_uvicorn_access.addHandler.call_count == 2
    mock_uvicorn_access.setLevel.assert_called_with("DEBUG")

    # Check propagation is set to False for uvicorn.access
    assert mock_uvicorn_access.propagate is False


@patch("yai_nexus_logger.uvicorn_support.logging.getLogger")
def test_configure_uvicorn_logging_with_queued_handler(mock_getLogger):
    """
    Test that configure_uvicorn_logging works correctly with QueuedLogHandler
    and only processes StreamHandler for uvicorn.access.
    """
    # Arrange
    mock_uvicorn_access = MagicMock()

    def getitem(name):
        if name == "uvicorn.access":
            return mock_uvicorn_access
        return MagicMock()

    mock_getLogger.side_effect = getitem

    # Create a mock QueuedLogHandler (not a StreamHandler)
    mock_queued_handler = MagicMock()

    # Create a regular StreamHandler for comparison
    mock_stream_handler = logging.StreamHandler()

    handlers = [mock_stream_handler, mock_queued_handler]
    level = "INFO"

    # Act - This should not raise an AttributeError
    configure_uvicorn_logging(handlers=handlers, level=level)

    # Assert
    # Check that only uvicorn.access handler was cleared and configured
    mock_uvicorn_access.handlers.clear.assert_called_once()
    # Only the StreamHandler should be copied for uvicorn.access (1 handler)
    # QueuedLogHandler should be ignored since it doesn't have stream attribute
    assert mock_uvicorn_access.addHandler.call_count == 1
    mock_uvicorn_access.setLevel.assert_called_with("INFO")

    # Check propagation is set to False for uvicorn.access
    assert mock_uvicorn_access.propagate is False
