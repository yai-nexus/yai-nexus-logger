# tests/yai_nexus_logger/integration/test_sls_integration.py

import os
from unittest.mock import patch, MagicMock
import pytest

from yai_nexus_logger import get_logger, trace_context
from yai_nexus_logger.internal.internal_handlers import SLS_SDK_AVAILABLE

# 仅在安装了 SLS 依赖时运行此文件中的所有测试
pytestmark = pytest.mark.skipif(not SLS_SDK_AVAILABLE, reason="SLS SDK not installed")


@pytest.fixture(autouse=True)
def reset_logger_config():
    """在每次测试前重置 logger 配置，确保环境干净"""
    # 这个 import 必须放在这里，以便在测试运行时重置
    from yai_nexus_logger import logger_builder
    
    # 使用 with patch.dict 来确保在测试期间 _initialized_loggers 是空的，
    # 并且在测试结束后恢复原状，避免对其他测试文件产生副作用。
    with patch.object(logger_builder, "_initialized_loggers", {}), \
         patch.object(logger_builder, "_is_configured", False):
        yield

# 我们现在模拟我们自己的 Handler 的 emit 方法，这是集成测试的正确方式
@patch("yai_nexus_logger.internal.internal_handlers.SLSLogHandler.emit")
def test_sls_handler_sends_logs_with_mocked_backend(mock_emit):
    """
    测试 get_logger 配置的 SLS handler 是否会尝试发送日志。
    我们 mock 了 handler 的 emit 方法，所以不会真的发送数据。
    """
    sls_env_vars = {
        "LOG_APP_NAME": "sls_integration_test",
        "LOG_LEVEL": "INFO",
        "SLS_ENABLED": "true",
        "SLS_ENDPOINT": "fake-endpoint.log.aliyuncs.com",
        "SLS_ACCESS_KEY_ID": "fake_id",
        "SLS_ACCESS_KEY_SECRET": "fake_secret",
        "SLS_PROJECT": "fake_project",
        "SLS_LOGSTORE": "fake_logstore",
        "SLS_TOPIC": "test_topic",
    }
    
    # 使用 patch.dict 来临时设置环境变量
    with patch.dict(os.environ, sls_env_vars):
        logger = get_logger("sls_integration_logger")
        
        trace_id = "trace-for-sls-test"
        trace_context.set_trace_id(trace_id)

        test_message = "This is a message for SLS."
        logger.warning(test_message)

    # 验证我们的 handler 的 "emit" 方法被呼叫了一次
    mock_emit.assert_called_once()
    
    # (可选) 深入检查传递给 emit 的内容
    log_record = mock_emit.call_args[0][0]
    assert test_message in log_record.getMessage()
    assert log_record.levelname == "WARNING"


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
        pytest.fail("python-dotenv is not installed. Please run 'pip install python-dotenv'")

    # 再次检查所有必要的环境变量是否都已加载
    required_vars = [
        "SLS_ENDPOINT", "SLS_ACCESS_KEY_ID", "SLS_ACCESS_KEY_SECRET",
        "SLS_PROJECT", "SLS_LOGSTORE"
    ]
    if any(not os.getenv(var) for var in required_vars):
        pytest.skip(f"Required SLS environment variables are not set in .env file: {required_vars}")

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
        from yai_nexus_logger.internal.internal_handlers import _shutdown_sls_handler
        _shutdown_sls_handler()

    except Exception as e:
        pytest.fail(f"Logging to SLS failed with an exception: {e}")
