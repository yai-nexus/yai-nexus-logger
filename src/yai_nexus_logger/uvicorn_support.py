"""Provides support for integrating the logger with Uvicorn's logging system."""

import logging
from typing import List

from uvicorn.logging import AccessFormatter

from yai_nexus_logger.trace_context import trace_context


class UvicornAccessFormatter(logging.Formatter):
    """
    Custom formatter for Uvicorn access logs to include the trace_id.
    It wraps Uvicorn's default AccessFormatter and prepends the trace_id.
    """

    def __init__(self):
        super().__init__()
        self.access_formatter = AccessFormatter()

    def format(self, record: logging.LogRecord) -> str:
        """
        Formats the log message to include trace_id and other structured info.
        """
        access_log = self.access_formatter.format(record)

        # Get trace_id from context
        trace_id = trace_context.get_trace_id()
        trace_id_str = f"[{trace_id}]" if trace_id else "[No-Trace-ID]"

        # Our final format
        return f"{trace_id_str} | {access_log}"


def configure_uvicorn_logging(
    handlers: List[logging.Handler], level: str = "INFO"
) -> None:
    """
    Reconfigures the Uvicorn loggers to use the application's handlers.
    This ensures that Uvicorn's logs (access, error, and general) are
    processed by the same handlers as the application logger, providing
    a unified logging setup.

    Args:
        handlers (List[logging.Handler]): A list of logging handlers to attach.
        level (str): The logging level to set for the Uvicorn loggers.
    """
    # 1. Detach existing handlers from Uvicorn loggers
    for name in ["uvicorn", "uvicorn.error", "uvicorn.access"]:
        log = logging.getLogger(name)
        log.handlers.clear()
        log.propagate = False  # Prevent logs from propagating to the root logger

    # 2. Configure 'uvicorn.access' logger
    uvicorn_access_logger = logging.getLogger("uvicorn.access")
    # Replace the default formatter with our custom one
    for handler in handlers:
        # Create a copy of the handler to avoid side effects
        handler_copy = logging.StreamHandler(handler.stream)
        handler_copy.setFormatter(UvicornAccessFormatter())
        uvicorn_access_logger.addHandler(handler_copy)
    uvicorn_access_logger.setLevel(level.upper())

    # 3. Configure 'uvicorn' and 'uvicorn.error' loggers
    # These will use the formatters already attached to the handlers
    for name in ["uvicorn", "uvicorn.error"]:
        log = logging.getLogger(name)
        for handler in handlers:
            log.addHandler(handler)
        log.setLevel(level.upper())
