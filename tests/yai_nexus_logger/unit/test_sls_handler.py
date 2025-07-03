# tests/yai_nexus_logger/unit/test_sls_handler.py

from unittest.mock import MagicMock, patch
import pytest
import os
import logging

from yai_nexus_logger import get_logger
from yai_nexus_logger.internal.internal_handlers import SLS_SDK_AVAILABLE

# 使用 pytest.mark.skipif 来在未安装 SLS 依赖时跳过这些测试
pytestmark = pytest.mark.skipif(not SLS_SDK_AVAILABLE, reason="SLS SDK not installed")


@pytest.fixture(autouse=True)
def reset_logger_config():
    """在每次测试前重置 logger 配置，确保环境干净"""
    from yai_nexus_logger import logger_builder
    with patch.object(logger_builder, "_initialized_loggers", {}), \
         patch.object(logger_builder, "_is_configured", False):
        yield


# 我们现在模拟 get_sls_handler，这是 get_logger 的直接依赖
@patch("yai_nexus_logger.logger_builder.get_sls_handler")
def test_get_logger_with_sls_handler(mock_get_sls_handler):
    """
    测试 get_logger 在配置了 SLS 环境变量时，是否会正确调用 get_sls_handler
    并将返回的 handler 添加到 logger 中。
    """
    mock_handler_instance = MagicMock()
    mock_get_sls_handler.return_value = mock_handler_instance

    app_name = "sls_test_app"
    sls_env_vars = {
        "LOG_APP_NAME": app_name,
        "LOG_LEVEL": "INFO",
        "SLS_ENABLED": "true",
        "SLS_ENDPOINT": "fake-endpoint.log.aliyuncs.com",
        "SLS_ACCESS_KEY_ID": "fake_id",
        "SLS_ACCESS_KEY_SECRET": "fake_secret",
        "SLS_PROJECT": "fake_project",
        "SLS_LOGSTORE": "fake_logstore",
    }
    
    with patch.dict(os.environ, sls_env_vars):
        # 请求与 LOG_APP_NAME 同名的 logger，以获取根 logger
        logger = get_logger(app_name)

    mock_get_sls_handler.assert_called_once()
    
    # 根据新的设计，处理器是加在根 logger (app_name) 上的
    # 我们应该检查根 logger 的 handlers
    root_logger = logging.getLogger(app_name)
    assert mock_handler_instance in root_logger.handlers


@patch("yai_nexus_logger.logger_builder.SLS_SDK_AVAILABLE", False)
@patch("warnings.warn")
def test_get_logger_sls_import_error_graceful_fail(mock_warn):
    """
    测试在SLS SDK未安装时 (SLS_SDK_AVAILABLE=False)，
    get_logger 不会崩溃，而是会打印一个警告。
    """
    sls_env_vars = {
        "LOG_APP_NAME": "sls_fail_test_app",
        "SLS_ENABLED": "true", # 即使启用了SLS
        "SLS_ENDPOINT": "fake-endpoint.log.aliyuncs.com",
        "SLS_ACCESS_KEY_ID": "fake_id",
        "SLS_ACCESS_KEY_SECRET": "fake_secret",
        "SLS_PROJECT": "fake_project",
        "SLS_LOGSTORE": "fake_logstore",
    }
    
    with patch.dict(os.environ, sls_env_vars):
        try:
            get_logger("sls_fail_logger")
        except ImportError:
            pytest.fail("get_logger should not raise ImportError, but handle it gracefully.")

    # 验证是否调用了 warnings.warn 并发出了正确的警告信息
    mock_warn.assert_called_once()
    assert "aliyun-log-python-sdk is not installed" in mock_warn.call_args[0][0]