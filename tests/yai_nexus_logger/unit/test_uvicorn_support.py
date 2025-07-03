"""Unit tests for the yai_nexus_logger.uvicorn_support module."""

import logging
from unittest.mock import MagicMock, patch

import pytest
from uvicorn.logging import AccessFormatter

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
    Test that configure_uvicorn_logging correctly configures uvicorn loggers.
    """
    # Arrange
    mock_uvicorn_access = MagicMock()
    mock_uvicorn_error = MagicMock()
    mock_uvicorn_main = MagicMock()

    def getitem(name):
        if name == "uvicorn.access":
            return mock_uvicorn_access
        if name == "uvicorn.error":
            return mock_uvicorn_error
        if name == "uvicorn":
            return mock_uvicorn_main
        return MagicMock()

    mock_getLogger.side_effect = getitem

    mock_handler1 = logging.StreamHandler()
    mock_handler2 = logging.FileHandler("test.log")
    handlers = [mock_handler1, mock_handler2]
    level = "DEBUG"

    # Act
    configure_uvicorn_logging(handlers=handlers, level=level)

    # Assert
    # Check that handlers were cleared and new ones added
    mock_uvicorn_access.handlers.clear.assert_called_once()
    assert mock_uvicorn_access.addHandler.call_count == len(handlers)
    mock_uvicorn_access.setLevel.assert_called_with("DEBUG")

    mock_uvicorn_error.handlers.clear.assert_called_once()
    assert mock_uvicorn_error.addHandler.call_count == len(handlers)
    mock_uvicorn_error.setLevel.assert_called_with("DEBUG")

    mock_uvicorn_main.handlers.clear.assert_called_once()
    assert mock_uvicorn_main.addHandler.call_count == len(handlers)
    mock_uvicorn_main.setLevel.assert_called_with("DEBUG")

    # Check propagation is set to False
    assert mock_uvicorn_access.propagate is False
    assert mock_uvicorn_error.propagate is False
    assert mock_uvicorn_main.propagate is False 