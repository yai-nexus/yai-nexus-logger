"""
阿里云SLS（日志服务）使用示例

本示例展示如何使用 yai-nexus-logger 将日志发送到阿里云日志服务。

使用前请确保：
1. 已安装阿里云日志SDK: pip install 'yai-nexus-logger[sls]'
2. 已在阿里云创建了日志项目和日志库
3. 具有正确的访问密钥权限
"""

import logging
import uuid
from yai_nexus_logger import LoggerBuilder, trace_context

# 阿里云SLS配置信息 - 北京区域
# 从环境变量或.env文件读取SLS配置
import os
from dotenv import load_dotenv

# 加载.env文件中的环境变量
load_dotenv()

SLS_CONFIG = {
    "endpoint": os.getenv("SLS_ENDPOINT", "cn-beijing.log.aliyuncs.com"),
    "access_key_id": os.getenv("SLS_ACCESS_KEY_ID"),
    "access_key_secret": os.getenv("SLS_ACCESS_KEY_SECRET"),
    "project": os.getenv("SLS_PROJECT", "yai-log-test"),
    "logstore": os.getenv("SLS_LOGSTORE", "app-log"),
    "topic": os.getenv("SLS_TOPIC", "python_app"),
    "source": os.getenv("SLS_SOURCE", "example_app"),
}

# 验证必要的配置是否存在
required_keys = ["access_key_id", "access_key_secret"]
missing_keys = [key for key in required_keys if not SLS_CONFIG[key]]
if missing_keys:
    raise ValueError(f"缺少必要的SLS配置: {missing_keys}。请在.env文件中设置相应的环境变量。")


def basic_sls_example():
    """基础阿里云SLS日志示例"""
    print("=== 基础阿里云SLS日志示例 ===")
    
    # 创建带有SLS handler的logger
    logger = (
        LoggerBuilder(name="sls_app", level="INFO")
        .with_console_handler()  # 同时输出到控制台，方便查看
        .with_sls_handler(
            endpoint=SLS_CONFIG["endpoint"],
            access_key_id=SLS_CONFIG["access_key_id"],
            access_key_secret=SLS_CONFIG["access_key_secret"],
            project=SLS_CONFIG["project"],
            logstore=SLS_CONFIG["logstore"],
            topic=SLS_CONFIG["topic"],
            source=SLS_CONFIG["source"],
        )
        .build()
    )

    # 记录不同级别的日志
    logger.info("应用启动成功！这条日志会被发送到阿里云SLS")
    logger.warning("这是一条警告消息")
    logger.error("这是一条错误消息")

    # 记录包含额外信息的日志
    logger.info("用户登录", extra={"user_id": "12345", "action": "login"})


def trace_id_example():
    """带追踪ID的日志示例"""
    print("\n=== 带追踪ID的阿里云SLS日志示例 ===")
    
    logger = (
        LoggerBuilder(name="sls_app_trace", level="INFO")
        .with_console_handler()
        .with_sls_handler(
            endpoint=SLS_CONFIG["endpoint"],
            access_key_id=SLS_CONFIG["access_key_id"],
            access_key_secret=SLS_CONFIG["access_key_secret"],
            project=SLS_CONFIG["project"],
            logstore=SLS_CONFIG["logstore"],
            topic=SLS_CONFIG["topic"],
            source=SLS_CONFIG["source"],
        )
        .build()
    )

    # 模拟一个请求的处理过程
    request_id = str(uuid.uuid4())
    token = trace_context.set_trace_id(request_id)

    try:
        logger.info("开始处理用户请求")
        logger.info("验证用户权限")
        logger.info("执行业务逻辑")
        
        # 模拟一些处理...
        import time
        time.sleep(0.1)
        
        logger.info("请求处理完成")
        
    finally:
        # 清理trace_id
        trace_context.reset_trace_id(token)


def exception_logging_example():
    """异常日志示例"""
    print("\n=== 异常日志示例 ===")
    
    logger = (
        LoggerBuilder(name="sls_exception", level="DEBUG")
        .with_console_handler()
        .with_sls_handler(
            endpoint=SLS_CONFIG["endpoint"],
            access_key_id=SLS_CONFIG["access_key_id"],
            access_key_secret=SLS_CONFIG["access_key_secret"],
            project=SLS_CONFIG["project"],
            logstore=SLS_CONFIG["logstore"],
            topic="exceptions",  # 使用不同的topic来分类异常日志
            source=SLS_CONFIG["source"],
        )
        .build()
    )

    try:
        # 模拟一个会产生异常的操作
        result = 10 / 0
    except ZeroDivisionError as e:
        # 记录异常信息，exc_info=True 会包含完整的堆栈跟踪
        logger.error("除零错误发生！", exc_info=True)
        logger.error(f"错误详情: {str(e)}")


def multi_handler_example():
    """多个处理器示例：同时输出到控制台、文件和SLS"""
    print("\n=== 多处理器示例 ===")
    
    logger = (
        LoggerBuilder(name="multi_handler", level="DEBUG")
        .with_console_handler()                    # 输出到控制台
        .with_file_handler(path="logs/app.log")    # 输出到文件
        .with_sls_handler(                        # 输出到阿里云SLS
            endpoint=SLS_CONFIG["endpoint"],
            access_key_id=SLS_CONFIG["access_key_id"],
            access_key_secret=SLS_CONFIG["access_key_secret"],
            project=SLS_CONFIG["project"],
            logstore=SLS_CONFIG["logstore"],
            topic="multi_output",
            source=SLS_CONFIG["source"],
        )
        .build()
    )

    logger.debug("这条日志会同时出现在控制台、文件和阿里云SLS中")
    logger.info("多重输出让你可以灵活地管理日志")
    logger.warning("本地文件方便开发调试，SLS方便生产监控")


if __name__ == "__main__":
    print("阿里云SLS日志示例")
    print("注意：运行前请先配置正确的SLS_CONFIG信息！")
    print()
    
    # 验证配置（使用北京区域的真实配置）
    print(f"🔧 使用配置:")
    print(f"   区域: {SLS_CONFIG['endpoint']}")
    print(f"   项目: {SLS_CONFIG['project']}")
    print(f"   日志库: {SLS_CONFIG['logstore']}")
    print(f"   AccessKey: {SLS_CONFIG['access_key_id'][:8]}...")
    print()
    
    try:
        basic_sls_example()
        trace_id_example()
        exception_logging_example()
        multi_handler_example()
        
        print("\n✅ 所有示例运行完成！请登录阿里云日志服务控制台查看日志。")
        
    except ImportError as e:
        if "aliyun-log-python-sdk" in str(e):
            print("❌ 错误: 阿里云日志SDK未安装")
            print("请运行: pip install 'yai-nexus-logger[sls]'")
        else:
            raise
    except Exception as e:
        print(f"❌ 运行出错: {e}")
        print("请检查阿里云SLS配置是否正确") 