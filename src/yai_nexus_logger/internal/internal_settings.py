"""
Configuration settings for yai-nexus-logger.

This module centralizes all configuration settings that are read from
environment variables. This provides a single source of truth for configuration.
"""

import os


class Settings:
    """
    Encapsulates all configuration settings for the logger.
    Settings are read from environment variables when accessed, with sensible defaults.
    """

    @property
    def APP_NAME(self) -> str:
        return os.getenv("LOG_APP_NAME", "app")

    @property
    def LOG_LEVEL(self) -> str:
        return os.getenv("LOG_LEVEL", "INFO")

    @property
    def CONSOLE_ENABLED(self) -> bool:
        return os.getenv("LOG_CONSOLE_ENABLED", "true").lower() == "true"

    @property
    def FILE_ENABLED(self) -> bool:
        return os.getenv("LOG_FILE_ENABLED", "false").lower() == "true"

    @property
    def FILE_PATH(self) -> str:
        return os.getenv("LOG_FILE_PATH", f"logs/{self.APP_NAME}.log")

    @property
    def SLS_ENABLED(self) -> bool:
        return os.getenv("SLS_ENABLED", "false").lower() == "true"

    @property
    def SLS_ENDPOINT(self) -> str | None:
        return os.getenv("SLS_ENDPOINT")

    @property
    def SLS_ACCESS_KEY_ID(self) -> str | None:
        return os.getenv("SLS_ACCESS_KEY_ID")

    @property
    def SLS_ACCESS_KEY_SECRET(self) -> str | None:
        return os.getenv("SLS_ACCESS_KEY_SECRET")

    @property
    def SLS_PROJECT(self) -> str | None:
        return os.getenv("SLS_PROJECT")

    @property
    def SLS_LOGSTORE(self) -> str | None:
        return os.getenv("SLS_LOGSTORE")

    @property
    def SLS_TOPIC(self) -> str | None:
        return os.getenv("SLS_TOPIC")

    @property
    def SLS_SOURCE(self) -> str | None:
        return os.getenv("SLS_SOURCE")

    @property
    def UVICORN_INTEGRATION_ENABLED(self) -> bool:
        return os.getenv("LOG_UVICORN_INTEGRATION_ENABLED", "false").lower() == "true"


# Create a single instance to be used throughout the application
settings = Settings()
