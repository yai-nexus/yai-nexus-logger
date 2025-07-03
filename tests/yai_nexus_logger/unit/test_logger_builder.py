"""Unit tests for the LoggerBuilder."""

import logging
import os
from pathlib import Path

from yai_nexus_logger.logger_builder import LoggerBuilder


def test_builder_creates_logger_with_name_and_level():
    """测试构建器是否能正确设置名称和级别。"""
    logger = LoggerBuilder("test_logger", "DEBUG").build()
    assert logger.name == "test_logger"
    assert logger.level == logging.DEBUG


def test_builder_adds_console_handler():
    """测试 with_console_handler 是否能添加控制台处理器。"""
    logger = LoggerBuilder("console_test").with_console_handler().build()
    assert any(isinstance(h, logging.StreamHandler) for h in logger.handlers)


def test_builder_adds_file_handler():
    """测试 with_file_handler 是否能添加文件处理器。"""
    log_file = Path("logs/test_file_handler.log")
    if log_file.exists():
        os.remove(log_file)

    logger = LoggerBuilder("file_test").with_file_handler(path=str(log_file)).build()
    assert any(
        isinstance(h, logging.handlers.TimedRotatingFileHandler)
        for h in logger.handlers
    )

    # 验证文件是否已创建
    logger.warning("This should create a file.")
    assert log_file.exists()
    os.remove(log_file)


def test_builder_builds_with_default_handler_if_none_configured():
    """测试如果没有配置处理器，build() 是否会默认添加控制台处理器。"""
    logger = LoggerBuilder("default_handler_test").build()
    assert len(logger.handlers) == 1
    assert isinstance(logger.handlers[0], logging.StreamHandler)


def test_builder_is_fluent():
    """测试构建器方法是否能链式调用。"""
    log_file = Path("logs/fluent_test.log")
    if log_file.exists():
        os.remove(log_file)

    builder = LoggerBuilder("fluent_test", "WARNING")
    returned_builder = builder.with_console_handler().with_file_handler(
        path=str(log_file)
    )

    assert returned_builder is builder

    logger = returned_builder.build()
    logger.error("Testing fluent build.")

    assert log_file.exists()
    os.remove(log_file)


def test_with_uvicorn_integration(mocker):
    """
    Test that with_uvicorn_integration() correctly triggers uvicorn configuration.
    """
    mock_configure_uvicorn = mocker.patch(
        "yai_nexus_logger.logger_builder.configure_uvicorn_logging"
    )

    builder = (
        LoggerBuilder("uvicorn_test", "DEBUG")
        .with_console_handler()
        .with_uvicorn_integration()
    )
    logger = builder.build()

    mock_configure_uvicorn.assert_called_once()
    # Verify it was called with the builder's handlers and level
    mock_configure_uvicorn.assert_called_with(
        handlers=logger.handlers, level="DEBUG"
    )
