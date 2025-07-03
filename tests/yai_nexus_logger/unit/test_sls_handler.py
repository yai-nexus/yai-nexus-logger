# tests/yai_nexus_logger/unit/test_sls_handler.py

import logging
from unittest.mock import patch

import pytest

from yai_nexus_logger.internal.internal_handlers import (
    SLS_SDK_AVAILABLE,
    SLSLogHandler,
    get_sls_handler,
)

# 使用 pytest.mark.skipif 来在未安装 SLS 依赖时跳过这些测试
pytestmark = pytest.mark.skipif(not SLS_SDK_AVAILABLE, reason="SLS SDK not installed")


@pytest.fixture(autouse=True)
def clean_logging_environment():
    """A helper to ensure a clean logging state before each test."""
    # 清除 root logger 的所有 handlers
    logging.root.handlers.clear()
    # 关闭所有现有的 loggers
    logging.shutdown()
    # 确保可以重新配置
    with patch("logging.Logger.hasHandlers", return_value=False):
        yield


# 我们现在模拟 get_sls_handler，这是 get_logger 的直接依赖
@pytest.mark.skipif(not SLS_SDK_AVAILABLE, reason="SLS SDK not installed")
@patch("yai_nexus_logger.internal.internal_handlers.LogClient")
def test_get_logger_with_sls_handler(mock_log_client):
    """测试 get_sls_handler 函数是否能正确创建一个配置好的 SLS handler"""
    formatter = logging.Formatter()
    handler = get_sls_handler(
        formatter=formatter,
        app_name="test_app",
        endpoint="ep",
        access_key_id="id",
        access_key_secret="secret",
        project="proj",
        logstore="log",
    )
    assert isinstance(handler, SLSLogHandler)
    assert handler.formatter is formatter
    mock_log_client.assert_called_with("ep", "id", "secret")


@pytest.mark.skipif(SLS_SDK_AVAILABLE, reason="SLS SDK is installed")
def test_get_logger_sls_import_error_graceful_fail():
    """在未安装 SLS SDK 时，测试 get_sls_handler 是否会引发 ImportError"""
    with pytest.raises(ImportError, match="SLS dependencies are not installed"):
        get_sls_handler(
            formatter=logging.Formatter(),
            app_name="test_app",
            endpoint="ep",
            access_key_id="id",
            access_key_secret="secret",
            project="proj",
            logstore="log",
        )
