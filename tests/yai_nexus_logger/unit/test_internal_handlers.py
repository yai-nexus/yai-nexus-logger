# tests/yai_nexus_logger/unit/test_internal_handlers.py

import logging
import sys
from unittest.mock import MagicMock, patch

import pytest

from yai_nexus_logger.internal.internal_handlers import (
    SLS_SDK_AVAILABLE,  # 导入我们新的可用性标志
    get_console_handler,
    get_file_handler,
    get_sls_handler,
)


@pytest.fixture
def mock_formatter():
    return MagicMock(spec=logging.Formatter)


def test_get_console_handler(mock_formatter):
    handler = get_console_handler(mock_formatter)
    assert isinstance(handler, logging.StreamHandler)
    assert handler.stream == sys.stdout
    assert handler.formatter == mock_formatter


def test_get_file_handler_creates_directory(mock_formatter, tmp_path):
    """
    测试 get_file_handler 是否能在目录不存在时自动创建它。
    """
    log_dir = tmp_path / "test_logs"
    log_file = log_dir / "app.log"

    assert not log_dir.exists()

    handler = get_file_handler(
        formatter=mock_formatter,
        path=str(log_file),
        when="D",
        interval=1,
        backup_count=1,
    )

    assert log_dir.exists()
    assert isinstance(handler, logging.handlers.TimedRotatingFileHandler)


# 使用 pytest.mark.skipif 来在未安装 SLS 依赖时跳过此测试
@pytest.mark.skipif(not SLS_SDK_AVAILABLE, reason="SLS SDK not installed")
# 我们现在模拟自己创建的 SLSLogHandler
@patch("yai_nexus_logger.internal.internal_handlers.SLSLogHandler")
def test_get_sls_handler_initialization(MockSLSLogHandler, mock_formatter):
    """
    测试 get_sls_handler 是否用正确的参数初始化了我们自定义的 SLSLogHandler。
    """
    # 模拟我们自定义 Handler 的返回实例
    mock_handler_instance = MockSLSLogHandler.return_value
    mock_handler_instance.setFormatter = MagicMock()  # 模拟 setFormatter 方法

    handler = get_sls_handler(
        formatter=mock_formatter,
        app_name="test_app",
        endpoint="fake_endpoint",
        access_key_id="fake_id",
        access_key_secret="fake_secret",
        project="fake_project",
        logstore="fake_logstore",
        topic="custom_topic",  # 增加一个自定义 topic
    )

    # 验证 SLSLogHandler 是否用正确的参数被初始化
    MockSLSLogHandler.assert_called_once_with(
        endpoint="fake_endpoint",
        access_key_id="fake_id",
        access_key_secret="fake_secret",
        project="fake_project",
        logstore="fake_logstore",
        topic="custom_topic",  # 确认 topic 参数被正确传递
        source=None,
    )

    # 验证 setFormatter 方法被调用
    mock_handler_instance.setFormatter.assert_called_once_with(mock_formatter)

    # 验证返回的 handler 就是我们模拟的那个实例
    assert handler == mock_handler_instance
