"""
阿里云SLS（日志服务）使用示例

本示例展示如何使用 yai-nexus-logger 将日志发送到阿里云日志服务。

使用前请确保：
1. 已安装阿里云日志SDK: pip install 'yai-nexus-logger[sls]'
2. 已在阿里云创建了日志项目和日志库
3. 具有正确的访问密钥权限
"""

import logging
import os
import time
import uuid
from logging.handlers import TimedRotatingFileHandler

from yai_nexus_logger import LoggerConfigurator, init_logging, get_logger, trace_context

# 阿里云SLS配置信息 - 北京区域
# 从环境变量或.env文件读取SLS配置
from dotenv import load_dotenv

# 加载.env文件中的环境变量
load_dotenv()



def simple_sls_logging():
    """演示基本的 SLS 日志记录功能。"""
    print("\n--- 演示: 基本 SLS 日志 ---")
    init_logging()
    logger = get_logger()

    # 记录不同级别的日志
    logger.info("应用启动成功！这条日志会被发送到阿里云SLS")
    logger.warning("这是一条警告消息")
    logger.error("这是一条错误消息")

    # 记录包含额外信息的日志
    logger.info("用户登录", extra={"user_id": "12345", "action": "login"})


def sls_with_trace_id():
    """演示如何结合 trace_id 进行日志记录，这对于分布式系统追踪至关重要。"""
    print("\n--- 演示: 带 trace_id 的 SLS 日志 ---")
    init_logging()
    logger = get_logger()

    # 模拟一个请求的处理过程
    request_id = str(uuid.uuid4())
    token = trace_context.set_trace_id(request_id)

    try:
        logger.info("开始处理用户请求")
        logger.info("验证用户权限")
        logger.info("执行业务逻辑")
        
        # 模拟一些处理...
        time.sleep(0.1)
        
        logger.info("请求处理完成")
        
    finally:
        # 清理trace_id
        trace_context.reset_trace_id(token)


def sls_with_exception():
    """演示如何在捕获异常时记录日志，包括堆栈信息。"""
    print("\n--- 演示: 记录异常信息到 SLS ---")
    init_logging()
    logger = get_logger()

    try:
        # 模拟一个会产生异常的操作
        result = 10 / 0
    except ZeroDivisionError as e:
        # 记录异常信息，exc_info=True 会包含完整的堆栈跟踪
        logger.error("除零错误发生！", exc_info=True)
        logger.error(f"错误详情: {str(e)}")


def sls_with_multiple_handlers():
    """演示如何同时将日志发送到 SLS、控制台和文件。"""
    print("\n--- 演示: 多 Handler (SLS, Console, File) ---")
    init_logging()
    logger = get_logger()

    logger.debug("这条日志会同时出现在控制台、文件和阿里云SLS中")
    logger.info("多重输出让你可以灵活地管理日志")
    logger.warning("本地文件方便开发调试，SLS方便生产监控")


if __name__ == "__main__":
        try:
            simple_sls_logging()
            sls_with_trace_id()
            sls_with_exception()
            sls_with_multiple_handlers()
            
            print("\n✅ 所有示例运行完成！请登录阿里云日志服务控制台查看日志。")
        finally:
            # 确保所有日志都被发送
            logging.shutdown() 