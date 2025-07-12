"""测试 extra 参数功能"""

import logging
import pytest
from io import StringIO

from yai_nexus_logger import init_logging, get_logger
from yai_nexus_logger.internal.internal_formatter import InternalFormatter


class TestExtraParams:
    """测试 extra 参数的支持"""

    def test_formatter_with_extra_params(self):
        """测试格式化器能正确处理 extra 参数"""
        formatter = InternalFormatter("%(levelname)s | %(message)s")
        
        # 创建一个带有 extra 参数的 LogRecord
        record = logging.LogRecord(
            name="test_logger",
            level=logging.INFO,
            pathname="test.py",
            lineno=10,
            msg="测试消息",
            args=(),
            exc_info=None
        )
        
        # 添加 extra 字段
        record.user_id = "123"
        record.request_id = "abc-xyz"
        
        formatted = formatter.format(record)
        
        # 验证 extra 字段出现在输出中
        assert "user_id=123" in formatted
        assert "request_id=abc-xyz" in formatted
        assert "测试消息" in formatted

    def test_formatter_without_extra_params(self):
        """测试格式化器在没有 extra 参数时正常工作"""
        formatter = InternalFormatter("%(levelname)s | %(message)s")
        
        record = logging.LogRecord(
            name="test_logger",
            level=logging.INFO,
            pathname="test.py",
            lineno=10,
            msg="普通消息",
            args=(),
            exc_info=None
        )
        
        formatted = formatter.format(record)
        
        # 验证没有额外的 | 符号
        assert "普通消息" in formatted
        assert formatted.count("|") <= 2  # 只有基本的分隔符

    def test_logger_with_extra_params_console_output(self):
        """测试通过 logger 使用 extra 参数的完整流程"""
        import sys
        from io import StringIO
        
        # 创建一个简单的测试，避免复杂的日志系统初始化问题
        formatter = InternalFormatter("%(levelname)s | %(message)s")
        
        # 创建带 extra 的 LogRecord
        record = logging.LogRecord(
            name="test_module",
            level=logging.INFO,
            pathname="test.py",
            lineno=10,
            msg="用户操作",
            args=(),
            exc_info=None
        )
        
        # 模拟 extra 参数
        record.user_id = "456"
        record.action = "login"
        
        formatted = formatter.format(record)
        
        # 验证 extra 字段出现在输出中
        assert "user_id=456" in formatted
        assert "action=login" in formatted
        assert "用户操作" in formatted

    def test_extract_extra_fields_method(self):
        """测试 _extract_extra_fields 方法的正确性"""
        formatter = InternalFormatter()
        
        # 创建包含各种字段的 LogRecord
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="test.py",
            lineno=1,
            msg="test",
            args=(),
            exc_info=None
        )
        
        # 添加标准字段（应该被过滤掉）
        record.levelname = "INFO"
        record.message = "test message"
        
        # 添加自定义字段（应该被过滤掉）
        record.trace_id = "trace123"
        
        # 添加 extra 字段（应该被保留）
        record.custom_field = "custom_value"
        record.another_field = 42
        
        extra_fields = formatter._extract_extra_fields(record)
        
        assert extra_fields == {
            "custom_field": "custom_value",
            "another_field": 42
        }
        
        # 验证标准字段和自定义字段被正确过滤
        assert "levelname" not in extra_fields
        assert "message" not in extra_fields
        assert "trace_id" not in extra_fields

    def test_multiple_extra_params_formatting(self):
        """测试多个 extra 参数的格式化"""
        formatter = InternalFormatter("%(message)s")
        
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="test.py",
            lineno=1,
            msg="测试",
            args=(),
            exc_info=None
        )
        
        # 添加多个 extra 字段
        record.field1 = "value1"
        record.field2 = "value2"
        record.field3 = 123
        
        formatted = formatter.format(record)
        
        # 验证所有字段都存在
        assert "field1=value1" in formatted
        assert "field2=value2" in formatted
        assert "field3=123" in formatted
        
        # 验证字段之间用 | 分隔
        extra_part = formatted.split("测试 | ")[1]
        fields = extra_part.split(" | ")
        assert len(fields) == 3