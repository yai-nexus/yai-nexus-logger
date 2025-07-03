"""An example of using yai-nexus-logger with a FastAPI application."""

from time import time
from typing import Callable

import uvicorn
from fastapi import FastAPI, Request, Response

# 从我们的库中导入
from yai_nexus_logger import (
    LoggerBuilder,
    trace_context,
)

# 1. 使用 LoggerBuilder 初始化 logger
#    通过 .with_uvicorn_integration() 自动接管 uvicorn 日志
logger = (
    LoggerBuilder(name="my-fastapi-app", level="DEBUG")
    .with_console_handler()
    .with_file_handler()
    .with_uvicorn_integration()
    .build()
)

app = FastAPI()


@app.middleware("http")
async def logging_middleware(request: Request, call_next: Callable) -> Response:
    """
    FastAPI 中间件，用于：
    1. 从请求头 'X-Trace-ID' 获取或生成一个新的 trace_id。
    2. 将 trace_id 设置到 context var 中，以便在应用的任何地方访问。
    3. 记录每个请求的耗时和状态。
    """
    # 尝试从请求头获取 trace_id，如果没有则 get_trace_id() 会自动生成一个新的
    trace_id = request.headers.get("X-Trace-ID") or trace_context.get_trace_id()

    # set_trace_id 会返回一个 token，用于稍后重置 context
    token = trace_context.set_trace_id(trace_id)

    start_time = time()

    try:
        response = await call_next(request)
        response.headers["X-Trace-ID"] = trace_context.get_trace_id()
        status_code = response.status_code
    except Exception as e:
        logger.exception("An unhandled exception occurred")
        status_code = 500
        response = Response(status_code=status_code)
        raise e
    finally:
        process_time = (time() - start_time) * 1000
        logger.info(
            '"%s %s" %s %.2fms',
            request.method,
            request.url.path,
            status_code,
            process_time,
        )
        # 请求结束时重置 trace_id，清理上下文
        trace_context.reset_trace_id(token)

    return response


@app.get("/")
async def read_root():
    """一个简单的根路径，演示日志记录。"""
    logger.info("Handling request for the root endpoint.")

    # 模拟一些业务逻辑
    try:
        result = 1 / 1
        logger.debug("Successful division operation, result: %s", result)
    except ZeroDivisionError:
        logger.error("Attempted to divide by zero!", exc_info=True)

    logger.info("Finished handling root endpoint.")
    return {"message": "Hello from yai-nexus-logger!"}


@app.get("/error")
async def trigger_error():
    """一个触发错误的路径，用于演示异常日志。"""
    try:
        # 故意引发一个异常
        raise ValueError("This is a test error for logging.")
    except ValueError:
        # exc_info=True 会让 logger 自动捕获并记录异常信息和堆栈
        logger.error("Caught an expected ValueError.", exc_info=True)
    return {"message": "Error endpoint triggered and logged."}


if __name__ == "__main__":
    # 启动 uvicorn 服务器
    # logger 会自动处理 uvicorn 的日志，所以不再需要 log_config
    uvicorn.run(
        "fastapi_example:app",
        host="127.0.0.1",
        port=8000,
        reload=True,
    )
