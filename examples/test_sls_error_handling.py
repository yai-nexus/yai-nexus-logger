"""
测试 SLS Handler 错误处理机制

本脚本故意使用错误的 SLS 配置来触发异常，
验证新的错误处理逻辑是否能够正确显示异常信息。
"""

import logging
import os

from yai_nexus_logger import get_logger, init_logging, trace_context


def test_with_invalid_credentials():
    """测试：使用无效的凭据"""
    print("\n=== 测试 1: 无效凭据 ===")
    
    # 保存原始配置
    original_key = os.environ.get('SLS_ACCESS_KEY_SECRET')
    
    try:
        # 设置错误的凭据
        os.environ['SLS_ENABLED'] = 'true'
        os.environ['SLS_ACCESS_KEY_SECRET'] = 'invalid_secret_key'
        
        init_logging()
        logger = get_logger('test_invalid_creds')
        
        logger.info("这条日志应该发送失败，并显示详细的错误信息")
        logger.error("测试错误级别的日志")
        
    finally:
        # 恢复原始配置
        if original_key:
            os.environ['SLS_ACCESS_KEY_SECRET'] = original_key
        else:
            os.environ.pop('SLS_ACCESS_KEY_SECRET', None)


def test_with_invalid_endpoint():
    """测试：使用无效的端点"""
    print("\n=== 测试 2: 无效端点 ===")
    
    # 保存原始配置
    original_endpoint = os.environ.get('SLS_ENDPOINT')
    
    try:
        # 设置错误的端点
        os.environ['SLS_ENABLED'] = 'true'
        os.environ['SLS_ENDPOINT'] = 'invalid.endpoint.com'
        
        # 重置logging，因为之前已经初始化过
        logging.getLogger('app').handlers.clear()
        
        init_logging()
        logger = get_logger('test_invalid_endpoint')
        
        logger.info("这条日志也应该发送失败")
        
    finally:
        # 恢复原始配置
        if original_endpoint:
            os.environ['SLS_ENDPOINT'] = original_endpoint
        else:
            os.environ.pop('SLS_ENDPOINT', None)


def test_with_trace_id():
    """测试：带 trace_id 的错误处理"""
    print("\n=== 测试 3: 带 trace_id 的错误 ===")
    
    # 保存原始配置
    original_project = os.environ.get('SLS_PROJECT')
    
    try:
        # 设置错误的项目名
        os.environ['SLS_ENABLED'] = 'true'
        os.environ['SLS_PROJECT'] = 'nonexistent_project'
        
        # 重置logging
        logging.getLogger('app').handlers.clear()
        
        init_logging()
        logger = get_logger('test_trace_id')
        
        # 设置 trace_id
        token = trace_context.set_trace_id('test-trace-12345')
        
        try:
            logger.warning("带有 trace_id 的失败日志")
            logger.error("另一条错误日志", extra={'custom_field': 'custom_value'})
        finally:
            trace_context.reset_trace_id(token)
            
    finally:
        # 恢复原始配置
        if original_project:
            os.environ['SLS_PROJECT'] = original_project
        else:
            os.environ.pop('SLS_PROJECT', None)


def main():
    """主函数"""
    print("🧪 开始测试 SLS 错误处理机制...")
    print("预期行为：每个测试都会显示详细的错误信息到 stderr")
    print("错误信息应该包含异常类型、异常消息、SLS配置和原始日志内容")
    
    test_with_invalid_credentials()
    test_with_invalid_endpoint()
    test_with_trace_id()
    
    print("\n🧪 测试完成！")
    print("请检查上方的 stderr 输出，确认错误信息格式是否清晰明了。")


if __name__ == "__main__":
    main() 