"""
SLS Handler exc_info 和消息格式化的集成测试
"""

import logging
from unittest.mock import Mock, patch

from yai_nexus_logger import get_logger, init_logging, trace_context


class TestSLSExcInfoIntegration:
    """SLS Handler 异常信息和消息格式化的集成测试"""

    def setup_method(self):
        """每个测试前的设置"""
        # 清理现有的日志配置
        for name in ['app', 'test_sls_exc_info_integration']:
            logger = logging.getLogger(name)
            if logger.hasHandlers():
                logger.handlers.clear()
            logger.propagate = True

    @patch.dict('os.environ', {
        'SLS_ENABLED': 'true',
        'LOG_CONSOLE_ENABLED': 'false',
        'LOG_FILE_ENABLED': 'false',
        'SLS_ENDPOINT': 'test-endpoint',
        'SLS_ACCESS_KEY_ID': 'test-key',
        'SLS_ACCESS_KEY_SECRET': 'test-secret',
        'SLS_PROJECT': 'test-project',
        'SLS_LOGSTORE': 'test-logstore'
    })
    def test_logger_with_exc_info_and_formatting_integration(self):
        """测试通过 logger 接口使用 exc_info 和消息格式化"""

        # 模拟 SLS 客户端
        with patch('yai_nexus_logger.internal.internal_sls_handler.QueuedLogHandler') as mock_queued_handler_class:
            mock_handler = Mock()
            mock_handler.level = logging.DEBUG  # 设置日志级别
            mock_handler.setFormatter = Mock()  # 模拟 setFormatter 方法
            mock_queued_handler_class.return_value = mock_handler

            # 强制清理已存在的 handlers，确保重新初始化
            app_logger = logging.getLogger("app")
            app_logger.handlers.clear()

            # 模拟 hasHandlers 返回 False，强制重新初始化
            with patch.object(app_logger, 'hasHandlers', return_value=False):
                # 初始化日志系统
                init_logging()
                logger = get_logger(__name__)

                # 设置 trace_id
                token = trace_context.set_trace_id("test-trace-123")

                try:
                    # 测试异常记录
                    try:
                        raise ValueError("测试异常消息")
                    except ValueError:
                        logger.error(
                            "业务操作失败: user_id=%s, operation=%s, amount=%.2f",
                            "user123", "payment", 100.50,
                            exc_info=True
                        )

                    # 验证 SLS handler 被调用
                    assert mock_handler.emit.called
                    # 获取传递给 emit 的 LogRecord
                    call_args = mock_handler.emit.call_args[0]
                    log_record = call_args[0]

                    # 验证基础字段
                    assert "业务操作失败: user_id=user123, operation=payment, amount=100.50" in log_record.getMessage()
                    assert log_record.levelname == "ERROR"
                    assert hasattr(log_record, 'trace_id')
                    assert log_record.trace_id == "test-trace-123"

                    # 验证异常信息存在
                    assert log_record.exc_info is not None
                    assert log_record.exc_text is not None or log_record.exc_info is not None

                finally:
                    trace_context.reset_trace_id(token)

    @patch.dict('os.environ', {
        'SLS_ENABLED': 'true',
        'LOG_CONSOLE_ENABLED': 'false',
        'LOG_FILE_ENABLED': 'false',
        'SLS_ENDPOINT': 'test-endpoint',
        'SLS_ACCESS_KEY_ID': 'test-key',
        'SLS_ACCESS_KEY_SECRET': 'test-secret',
        'SLS_PROJECT': 'test-project',
        'SLS_LOGSTORE': 'test-logstore'
    })
    def test_multiple_log_calls_with_different_formatting(self):
        """测试多次日志调用使用不同的消息格式化"""

        # 模拟 SLS 客户端
        with patch('yai_nexus_logger.internal.internal_sls_handler.QueuedLogHandler') as mock_queued_handler_class:
            mock_handler = Mock()
            mock_handler.level = logging.DEBUG  # 设置日志级别
            mock_handler.setFormatter = Mock()  # 模拟 setFormatter 方法
            mock_queued_handler_class.return_value = mock_handler

            # 强制清理已存在的 handlers，确保重新初始化
            app_logger = logging.getLogger("app")
            app_logger.handlers.clear()

            # 模拟 hasHandlers 返回 False，强制重新初始化
            with patch.object(app_logger, 'hasHandlers', return_value=False):
                # 初始化日志系统
                init_logging()
                logger = get_logger(__name__)

                # 第一次调用：用户登录
                logger.info("用户登录成功: user_id=%s, ip=%s, user_agent=%s",
                           "user123", "192.168.1.100", "Chrome/91.0")

                # 第二次调用：系统监控
                logger.warning("系统资源警告: cpu_usage=%.1f%%, memory_usage=%.1f%%, component=%s",
                              85.2, 78.5, "web_server")

                # 验证两次调用都成功
                assert mock_handler.emit.call_count == 2

                # 验证第一次调用
                first_call_args = mock_handler.emit.call_args_list[0][0]
                first_record = first_call_args[0]

                expected_first_message = "用户登录成功: user_id=user123, ip=192.168.1.100, user_agent=Chrome/91.0"
                assert first_record.getMessage() == expected_first_message

                # 验证第二次调用
                second_call_args = mock_handler.emit.call_args_list[1][0]
                second_record = second_call_args[0]

                expected_second_message = "系统资源警告: cpu_usage=85.2%, memory_usage=78.5%, component=web_server"
                assert second_record.getMessage() == expected_second_message

    def teardown_method(self):
        """每个测试后的清理"""
        # 清理环境变量和日志配置
        for name in ['app', 'test_sls_exc_info_integration']:
            logger = logging.getLogger(name)
            if logger.hasHandlers():
                logger.handlers.clear()
                logger.propagate = True
