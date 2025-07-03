"""
yai-nexus-logger 基础使用示例

本示例展示了如何以最简单的方式初始化和使用日志器。
"""

from yai_nexus_logger import get_logger, init_logging


def main():
    """主函数，演示基本日志记录。"""
    # 1. 初始化日志系统
    # 默认情况下，会自动配置一个控制台处理器
    init_logging()

    # 2. 获取一个日志器实例
    # 推荐使用 __name__ 作为日志器名称，这样可以清晰地看到日志来源
    logger = get_logger(__name__)

    # 3. 记录不同级别的日志
    print("\n--- 记录基本日志消息 ---")
    logger.info("这是一条信息级别的日志。")
    logger.warning("这是一条警告级别的日志。")
    logger.error("这是一个错误级别的日志。")

    # 4. 记录包含额外结构化数据的日志
    print("\n--- 记录带额外数据的日志 ---")
    logger.info("用户操作记录", extra={"user_id": "test_user", "action": "login"})


if __name__ == "__main__":
    main()
    print("\n✅ 基础示例运行完成！")
