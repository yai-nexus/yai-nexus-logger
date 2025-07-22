# tests/yai_nexus_logger/integration/test_sls_integration.py

import logging
import os
from unittest.mock import patch

import pytest

from yai_nexus_logger import get_logger
from yai_nexus_logger.internal.internal_sls_handler import (
    SLS_SDK_AVAILABLE,
)

# 仅在安装了 SLS 依赖时运行此文件中的所有测试
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


# 标记这个测试需要一个特殊的环境变量来运行，避免在 CI/CD 环境中自动执行
@pytest.mark.skipif(
    os.getenv("RUN_REAL_SLS_TESTS", "false").lower() != "true",
    reason="RUN_REAL_SLS_TESTS is not set to 'true'",
)
def test_real_sls_logging_from_dotenv():
    """
    一个真实的端到端测试，它会：
    1. 从 .env 文件加载环境变量。
    2. 初始化一个真实的 SLS logger。
    3. 发送一条日志到阿里云。
    这个测试本身不验证日志是否到达，但如果过程中没有报错，就视为通过。
    你需要手动在阿里云SLS控制台确认日志是否成功送达。
    """
    try:
        from dotenv import load_dotenv

        # 从项目根目录的 .env 文件加载变量
        load_dotenv()
    except ImportError:
        pytest.fail(
            "python-dotenv is not installed. Please run 'pip install python-dotenv'"
        )

    # 再次检查所有必要的环境变量是否都已加载
    required_vars = [
        "SLS_ENDPOINT",
        "SLS_ACCESS_KEY_ID",
        "SLS_ACCESS_KEY_SECRET",
        "SLS_PROJECT",
        "SLS_LOGSTORE",
    ]
    if any(not os.getenv(var) for var in required_vars):
        pytest.skip(
            f"Required SLS environment variables are not set in .env file: {required_vars}"
        )

    # 为了这个测试，我们需要设置 SLS_ENABLED 为 true
    os.environ["SLS_ENABLED"] = "true"
    os.environ["LOG_APP_NAME"] = "real_sls_test_app"

    # 获取 logger
    logger = get_logger(__name__)

    import uuid

    unique_id = str(uuid.uuid4())
    test_message = f"This is a real test message to SLS with unique_id: {unique_id}"

    print(f"\nSending log to SLS. Check for message with ID: {unique_id}")

    try:
        logger.warning(test_message)
        # SlsHandler 是异步发送的，这里需要等待一下，确保日志有机会被发送出去
        logging.shutdown()

    except Exception as e:
        pytest.fail(f"Logging to SLS failed with an exception: {e}")
