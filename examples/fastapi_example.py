"""An example of using yai-nexus-logger with a FastAPI application."""

import uvicorn
from fastapi import FastAPI

# 从我们的库中导入
from yai_nexus_logger import (
    LoggerConfigurator,
    get_logger,
    init_logging,
)


# --- 应用设置 ---
# 将日志配置和应用创建封装到函数中，以避免在导入时执行
def create_app() -> FastAPI:
    # 在应用启动时配置日志
    # 可以通过环境变量或代码进行配置
    configurator = (
        LoggerConfigurator(level="DEBUG")
        .with_console_handler()
        .with_uvicorn_integration()
    )
    init_logging(configurator)

    logger = get_logger(__name__)
    app = FastAPI()

    @app.get("/")
    def read_root():
        """根路由，记录一条普通信息。"""
        logger.info("This is an info message from the root endpoint.")
        return {"message": "Hello World"}

    @app.get("/items/{item_id}")
    def read_item(item_id: int, q: str | None = None):
        """
        物品路由，记录包含参数的调试信息。
        """
        logger.debug(f"Fetching item {item_id} with query: {q}")
        if item_id == 42:
            logger.warning("Warning: You've requested the magic item!")
        return {"item_id": item_id, "q": q}

    @app.get("/error")
    def trigger_error():
        """
        错误路由，记录一条异常信息。
        """
        try:
            result = 1 / 0
        except ZeroDivisionError:
            logger.exception("An error occurred: Division by zero.")
        return {"message": "An error was logged."}

    return app


if __name__ == "__main__":
    # 在 __main__ 块中创建和运行 app
    app = create_app()
    # 使用 uvicorn 运行应用
    # uvicorn 会自动使用我们在 setup_logging 中通过 LOG_UVICORN_INTEGRATION_ENABLED 配置的日志格式
    uvicorn.run(app, host="0.0.0.0", port=8000)
