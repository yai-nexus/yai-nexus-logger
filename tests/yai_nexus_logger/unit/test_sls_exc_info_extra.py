"""
测试 SLS Handler 处理 exc_info 和消息格式化的功能
"""

import logging
from unittest.mock import Mock, patch

from yai_nexus_logger.internal.internal_sls_handler import get_sls_handler


class TestSLSHandlerExcInfoAndFormatting:
    """测试 SLS Handler 的 exc_info 和消息格式化处理"""

    def setup_method(self):
        """每个测试前的设置"""
        # 模拟 SLS 客户端
        self.mock_client = Mock()

        # 创建 handler 但使用模拟的客户端
        with patch('yai_nexus_logger.internal.internal_sls_handler.QueuedLogHandler') as mock_handler_class:
            mock_handler_instance = Mock()
            mock_handler_class.return_value = mock_handler_instance

            self.handler = get_sls_handler(
                formatter=logging.Formatter(),
                app_name="test-app",
                endpoint="test-endpoint",
                access_key_id="test-key",
                access_key_secret="test-secret",
                project="test-project",
                logstore="test-logstore"
            )
            # 替换内部的客户端为我们的模拟对象
            self.handler.client = self.mock_client

    def test_exc_info_is_included(self):
        """测试异常信息是否被正确包含"""
        # 创建一个带异常信息的日志记录
        try:
            1 / 0
        except ZeroDivisionError:
            import sys
            record = logging.LogRecord(
                name="test",
                level=logging.ERROR,
                pathname="test.py",
                lineno=10,
                msg="Test error with exception",
                args=(),
                exc_info=sys.exc_info()  # 使用实际的异常信息元组
            )

            # 发送日志
            self.handler.emit(record)

            # 验证 put_logs 被调用
            assert self.mock_client.put_logs.called

            # 获取发送的数据
            call_args = self.mock_client.put_logs.call_args[0][0]
            log_item = call_args.logitems[0]

            # 验证 contents 中包含异常信息
            contents_dict = dict(log_item.contents)
            assert "exception" in contents_dict
            assert "ZeroDivisionError" in contents_dict["exception"]
            assert "Traceback" in contents_dict["exception"]

    def test_message_formatting_with_args(self):
        """测试消息格式化功能"""
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="test.py",
            lineno=10,
            msg="用户操作: user_id=%s, action=%s, status=%s",
            args=("12345", "login", "success"),
            exc_info=None
        )

        # 发送日志
        self.handler.emit(record)

        # 获取发送的数据
        call_args = self.mock_client.put_logs.call_args[0][0]
        log_item = call_args.logitems[0]
        contents_dict = dict(log_item.contents)

        # 验证消息被正确格式化
        assert contents_dict["message"] == "用户操作: user_id=12345, action=login, status=success"

    def test_exc_info_with_formatted_message(self):
        """测试同时包含异常信息和格式化消息"""
        try:
            raise ValueError("Test exception")
        except ValueError:
            import sys
            record = logging.LogRecord(
                name="test",
                level=logging.ERROR,
                pathname="test.py",
                lineno=10,
                msg="操作失败: operation=%s, user=%s",
                args=("payment", "user123"),
                exc_info=sys.exc_info()
            )

            # 发送日志
            self.handler.emit(record)

            # 验证 put_logs 被调用
            assert self.mock_client.put_logs.called

            # 获取发送的数据
            call_args = self.mock_client.put_logs.call_args[0][0]
            log_item = call_args.logitems[0]

            # 验证 contents 中包含异常信息和格式化消息
            contents_dict = dict(log_item.contents)

            # 检查格式化后的消息
            assert contents_dict["message"] == "操作失败: operation=payment, user=user123"

            # 检查异常信息
            assert "exception" in contents_dict
            assert "ValueError" in contents_dict["exception"]
            assert "Test exception" in contents_dict["exception"]

    def test_basic_message_without_formatting(self):
        """测试不需要格式化的基本消息"""
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="test.py",
            lineno=10,
            msg="应用启动成功",
            args=(),
            exc_info=None
        )

        # 发送日志
        self.handler.emit(record)

        # 获取发送的数据
        call_args = self.mock_client.put_logs.call_args[0][0]
        log_item = call_args.logitems[0]
        contents_dict = dict(log_item.contents)

        # 验证消息内容
        assert contents_dict["message"] == "应用启动成功"
        assert contents_dict["level"] == "INFO"
        assert contents_dict["logger"] == "test"

    def test_complex_formatting_with_mixed_types(self):
        """测试包含多种数据类型的复杂格式化"""
        record = logging.LogRecord(
            name="test",
            level=logging.WARNING,
            pathname="test.py",
            lineno=10,
            msg="系统监控: cpu_usage=%.1f%%, memory_usage=%d%%, active_users=%s",
            args=(85.7, 78, "1024"),
            exc_info=None
        )

        # 发送日志
        self.handler.emit(record)

        # 获取发送的数据
        call_args = self.mock_client.put_logs.call_args[0][0]
        log_item = call_args.logitems[0]
        contents_dict = dict(log_item.contents)

        # 验证复杂格式化的消息
        expected_message = "系统监控: cpu_usage=85.7%, memory_usage=78%, active_users=1024"
        assert contents_dict["message"] == expected_message
