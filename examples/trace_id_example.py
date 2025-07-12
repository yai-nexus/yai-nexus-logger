"""An example of using yai-nexus-logger with trace_id in a FastAPI application."""

import uuid
from typing import Callable

import uvicorn
from fastapi import FastAPI, Request, Response

# 从我们的库中导入
from yai_nexus_logger import (
    LoggerConfigurator,
    get_logger,
    init_logging,
    trace_context,
)


# --- 应用设置 ---
# 将日志配置和应用创建封装到函数中，以避免在导入时执行
def create_app() -> FastAPI:
    """
    创建并配置 FastAPI 应用实例。
    """
    # 在应用启动时配置日志
    configurator = (
        LoggerConfigurator(level="DEBUG")
        .with_console_handler()
        .with_file_handler(path="logs/trace_id_example.log")
        .with_uvicorn_integration()
    )
    init_logging(configurator)

    logger = get_logger(__name__)
    app = FastAPI()

    @app.middleware("http")
    async def trace_id_middleware(request: Request, call_next: Callable) -> Response:
        """
        中间件：为每个请求注入一个唯一的 trace_id。
        """
        trace_id = request.headers.get("X-Trace-ID", str(uuid.uuid4()))
        token = trace_context.set_trace_id(trace_id)
        logger.info(f"Request started for trace_id: {trace_id}")
        # 验证 trace_id 是否正确设置
        trace_id_get = trace_context.get_trace_id()
        logger.info(f"trace_id_get: {trace_id_get or 'None'}")

        response = await call_next(request)

        # 将 trace_id 添加到响应头中，以便客户端可以获取
        response.headers["X-Trace-ID"] = trace_id

        trace_context.reset_trace_id(token)
        return response

    @app.get("/")
    def read_root():
        """
        根路由，记录一条普通信息。
        """
        logger.info("This is an info message from the root endpoint.")
        return {"message": "Hello World"}

    return app


if __name__ == "__main__":
    # 在 __main__ 块中创建和运行 app
    app = create_app()
    # 使用 uvicorn 运行应用
    uvicorn.run(app, host="0.0.0.0", port=8001) 