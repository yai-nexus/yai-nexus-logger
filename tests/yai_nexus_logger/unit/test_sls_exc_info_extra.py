"""
测试 SLS Handler 处理 exc_info 和 extra 参数的功能
"""

import logging
import pytest
from unittest.mock import Mock, patch

from yai_nexus_logger.internal.internal_sls_handler import SLSLogHandler


class TestSLSHandlerExcInfoAndExtra:
    """测试 SLS Handler 的 exc_info 和 extra 参数处理"""

    def setup_method(self):
        """每个测试前的设置"""
        # 模拟 SLS 客户端
        self.mock_client = Mock()
        
        # 创建 handler 但使用模拟的客户端
        with patch('yai_nexus_logger.internal.internal_sls_handler.LogClient'):
            self.handler = SLSLogHandler(
                endpoint="test-endpoint",
                access_key_id="test-key",
                access_key_secret="test-secret",
                project="test-project",
                logstore="test-logstore"
            )
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

    def test_extra_fields_are_included(self):
        """测试额外字段是否被正确包含"""
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="test.py",
            lineno=10,
            msg="Test with extra fields",
            args=(),
            exc_info=None
        )
        
        # 添加额外字段
        record.user_id = "12345"
        record.action = "login"
        record.ip_address = "192.168.1.1"
        
        # 发送日志
        self.handler.emit(record)
        
        # 验证 put_logs 被调用
        assert self.mock_client.put_logs.called
        
        # 获取发送的数据
        call_args = self.mock_client.put_logs.call_args[0][0]
        log_item = call_args.logitems[0]
        
        # 验证 contents 中包含额外字段
        contents_dict = dict(log_item.contents)
        assert "extra_user_id" in contents_dict
        assert contents_dict["extra_user_id"] == "12345"
        assert "extra_action" in contents_dict
        assert contents_dict["extra_action"] == "login"
        assert "extra_ip_address" in contents_dict
        assert contents_dict["extra_ip_address"] == "192.168.1.1"

    def test_both_exc_info_and_extra(self):
        """测试同时包含异常信息和额外字段"""
        try:
            raise ValueError("Test exception")
        except ValueError:
            import sys
            record = logging.LogRecord(
                name="test",
                level=logging.ERROR,
                pathname="test.py",
                lineno=10,
                msg="Test with both exception and extra",
                args=(),
                exc_info=sys.exc_info()
            )
            
            # 添加额外字段
            record.operation = "test_operation"
            record.user_id = "test_user"
            
            # 发送日志
            self.handler.emit(record)
            
            # 验证 put_logs 被调用
            assert self.mock_client.put_logs.called
            
            # 获取发送的数据
            call_args = self.mock_client.put_logs.call_args[0][0]
            log_item = call_args.logitems[0]
            
            # 验证 contents 中包含异常信息和额外字段
            contents_dict = dict(log_item.contents)
            
            # 检查异常信息
            assert "exception" in contents_dict
            assert "ValueError" in contents_dict["exception"]
            assert "Test exception" in contents_dict["exception"]
            
            # 检查额外字段
            assert "extra_operation" in contents_dict
            assert contents_dict["extra_operation"] == "test_operation"
            assert "extra_user_id" in contents_dict
            assert contents_dict["extra_user_id"] == "test_user"

    def test_standard_fields_not_duplicated(self):
        """测试标准字段不会作为 extra 字段重复"""
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="test.py",
            lineno=10,
            msg="Test standard fields",
            args=(),
            exc_info=None
        )
        
        # 这些是标准字段，不应该作为 extra 字段出现
        record.custom_field = "should_appear"  # 这个应该出现
        
        # 发送日志
        self.handler.emit(record)
        
        # 获取发送的数据
        call_args = self.mock_client.put_logs.call_args[0][0]
        log_item = call_args.logitems[0]
        contents_dict = dict(log_item.contents)
        
        # 检查自定义字段出现
        assert "extra_custom_field" in contents_dict
        assert contents_dict["extra_custom_field"] == "should_appear"
        
        # 检查标准字段不会重复
        extra_keys = [key for key in contents_dict.keys() if key.startswith("extra_")]
        standard_field_names = ["name", "levelname", "module", "funcName", "lineno"]
        
        for field_name in standard_field_names:
            assert f"extra_{field_name}" not in extra_keys

    def test_message_formatting(self):
        """测试消息格式化功能"""
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="test.py",
            lineno=10,
            msg="Test message with %s and %d",
            args=("string", 42),
            exc_info=None
        )
        
        # 发送日志
        self.handler.emit(record)
        
        # 获取发送的数据
        call_args = self.mock_client.put_logs.call_args[0][0]
        log_item = call_args.logitems[0]
        contents_dict = dict(log_item.contents)
        
        # 验证消息被正确格式化
        assert contents_dict["message"] == "Test message with string and 42" 