#!/usr/bin/env python3
"""
验证 QueuedLogHandler 兼容性修复的集成测试
"""

import logging
import sys
from unittest.mock import MagicMock

# 模拟 QueuedLogHandler
class MockQueuedLogHandler(logging.Handler):
    """模拟 QueuedLogHandler，没有 stream 属性"""
    def __init__(self):
        super().__init__()
        # 故意不设置 stream 属性

    def emit(self, record):
        pass


def test_queued_handler_compatibility():
    """测试 QueuedLogHandler 兼容性"""
    print("测试 QueuedLogHandler 兼容性...")
    
    # 导入我们的模块
    from yai_nexus_logger.uvicorn_support import configure_uvicorn_logging
    
    # 创建不同类型的 handlers
    console_handler = logging.StreamHandler(sys.stdout)
    file_handler = logging.FileHandler("test.log")
    queued_handler = MockQueuedLogHandler()
    
    handlers = [console_handler, file_handler, queued_handler]
    
    try:
        # 这应该不会抛出 AttributeError
        configure_uvicorn_logging(handlers=handlers, level="INFO")
        print("✅ 成功！没有抛出 AttributeError")
        return True
    except AttributeError as e:
        print(f"❌ 失败！仍然抛出 AttributeError: {e}")
        return False
    except Exception as e:
        print(f"❌ 失败！抛出其他异常: {e}")
        return False


def test_only_console_handlers_processed():
    """测试只有控制台 handler 被处理"""
    print("测试只有控制台 handler 被处理...")
    
    from yai_nexus_logger.uvicorn_support import configure_uvicorn_logging
    
    # Mock logging.getLogger
    original_getLogger = logging.getLogger
    mock_uvicorn_access = MagicMock()
    
    def mock_getLogger(name):
        if name == "uvicorn.access":
            return mock_uvicorn_access
        return original_getLogger(name)
    
    logging.getLogger = mock_getLogger
    
    try:
        console_handler = logging.StreamHandler(sys.stdout)
        file_handler = logging.FileHandler("test.log")
        queued_handler = MockQueuedLogHandler()
        
        handlers = [console_handler, file_handler, queued_handler]
        
        configure_uvicorn_logging(handlers=handlers, level="INFO")
        
        # 应该只有 1 个 handler 被添加（只有 console_handler，不包括 file_handler 和 queued_handler）
        expected_calls = 1
        actual_calls = mock_uvicorn_access.addHandler.call_count
        
        if actual_calls == expected_calls:
            print(f"✅ 成功！只有 {actual_calls} 个控制台 handler 被处理")
            return True
        else:
            print(f"❌ 失败！期望 {expected_calls} 个 handler，实际处理了 {actual_calls} 个")
            return False
            
    finally:
        # 恢复原始的 getLogger
        logging.getLogger = original_getLogger


if __name__ == "__main__":
    print("开始验证 QueuedLogHandler 兼容性修复...")
    print("=" * 50)
    
    test1_passed = test_queued_handler_compatibility()
    print()
    test2_passed = test_only_console_handlers_processed()
    
    print()
    print("=" * 50)
    if test1_passed and test2_passed:
        print("🎉 所有测试通过！修复成功！")
        sys.exit(0)
    else:
        print("💥 测试失败！")
        sys.exit(1)
