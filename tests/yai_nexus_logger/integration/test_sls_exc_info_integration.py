"""
SLS Handler exc_info 和 extra 参数的集成测试
"""

import logging
import pytest
from unittest.mock import Mock, patch

from yai_nexus_logger import get_logger, init_logging, trace_context


class TestSLSExcInfoIntegration:
    """SLS Handler 异常信息和额外字段的集成测试"""

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
    @patch('yai_nexus_logger.internal.internal_sls_handler.LogClient')
    def test_logger_with_exc_info_and_extra_integration(self, mock_log_client_class):
        """测试通过 logger 接口使用 exc_info 和 extra 参数"""
        # 设置模拟客户端
        mock_client = Mock()
        mock_log_client_class.return_value = mock_client

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
                    "业务操作失败", 
                    exc_info=True,
                    extra={
                        "user_id": "user123",
                        "operation": "payment",
                        "amount": 100.50
                    }
                )

            # 验证 SLS 调用
            assert mock_client.put_logs.called
            call_args = mock_client.put_logs.call_args[0][0]
            log_item = call_args.logitems[0]
            contents_dict = dict(log_item.contents)

            # 验证基础字段
            assert contents_dict["message"] == "业务操作失败"
            assert contents_dict["level"] == "ERROR"
            assert contents_dict["trace_id"] == "test-trace-123"

            # 验证异常信息
            assert "exception" in contents_dict
            assert "ValueError" in contents_dict["exception"]
            assert "测试异常消息" in contents_dict["exception"]
            assert "Traceback" in contents_dict["exception"]

            # 验证额外字段
            assert "extra_user_id" in contents_dict
            assert contents_dict["extra_user_id"] == "user123"
            assert "extra_operation" in contents_dict
            assert contents_dict["extra_operation"] == "payment"
            assert "extra_amount" in contents_dict
            assert contents_dict["extra_amount"] == "100.5"

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
    @patch('yai_nexus_logger.internal.internal_sls_handler.LogClient')
    def test_multiple_log_calls_with_different_extras(self, mock_log_client_class):
        """测试多次日志调用使用不同的 extra 字段"""
        # 设置模拟客户端
        mock_client = Mock()
        mock_log_client_class.return_value = mock_client

        # 初始化日志系统
        init_logging()
        logger = get_logger(__name__)

        # 第一次调用：用户登录
        logger.info("用户登录成功", extra={
            "user_id": "user123",
            "ip": "192.168.1.100",
            "user_agent": "Chrome/91.0"
        })

        # 第二次调用：系统监控
        logger.warning("系统资源警告", extra={
            "cpu_usage": 85.2,
            "memory_usage": 78.5,
            "component": "web_server"
        })

        # 验证两次调用都成功
        assert mock_client.put_logs.call_count == 2

        # 验证第一次调用
        first_call_args = mock_client.put_logs.call_args_list[0][0][0]
        first_contents = dict(first_call_args.logitems[0].contents)
        
        assert first_contents["message"] == "用户登录成功"
        assert "extra_user_id" in first_contents
        assert first_contents["extra_user_id"] == "user123"
        assert "extra_ip" in first_contents
        assert first_contents["extra_ip"] == "192.168.1.100"

        # 验证第二次调用
        second_call_args = mock_client.put_logs.call_args_list[1][0][0]
        second_contents = dict(second_call_args.logitems[0].contents)
        
        assert second_contents["message"] == "系统资源警告"
        assert "extra_cpu_usage" in second_contents
        assert second_contents["extra_cpu_usage"] == "85.2"
        assert "extra_component" in second_contents
        assert second_contents["extra_component"] == "web_server"

        # 确保第一次的 extra 字段不会出现在第二次调用中
        assert "extra_user_id" not in second_contents
        assert "extra_ip" not in second_contents

    def teardown_method(self):
        """每个测试后的清理"""
        # 清理环境变量和日志配置
        logger = logging.getLogger("app")
        if logger.hasHandlers():
            logger.handlers.clear() 