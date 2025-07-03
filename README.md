# YAI Nexus Logger

[![PyPI version](https://badge.fury.io/py/yai-nexus-logger.svg)](https://badge.fury.io/py/yai-nexus-logger)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

一个为现代 Python 应用设计的、功能强大且易于使用的结构化日志记录器，内置 `trace_id` 支持，让分布式系统中的请求追踪变得轻而易举。

## 核心功能

- **流式配置 API**：使用 `LoggerBuilder`，通过链式调用轻松构建和配置您的 logger。
- **结构化日志**：默认输出结构化的字符串日志，易于机器解析和人类阅读。
- **自动追踪 ID**：通过 `contextvars` 自动管理 `trace_id`，无缝支持异步框架（如 FastAPI）。
- **日志轮转**：内置支持基于时间的日志文件轮转，防止日志文件无限增长。
- **Uvicorn 集成**：提供对 Uvicorn 访问日志的开箱即用的支持。
- **灵活的处理器**：轻松启用控制台（stdout）和文件日志记录。

## 安装

通过 pip 从 PyPI 安装：

```bash
pip install yai-nexus-logger
```

## 快速上手

以下是一个基本的示例，展示如何配置和使用 logger：

```python
import logging
from yai_nexus_logger import LoggerBuilder, trace_context

# 1. 使用 LoggerBuilder 构建 logger
# 可以在创建时指定名称和日志级别
logger = LoggerBuilder(name="my_app", level="DEBUG") \
    .with_console_handler() \
    .with_file_handler(path="logs/my_app.log") \
    .build()

# 2. (可选) 设置一个自定义的 trace_id
trace_id = "request-id-abc-123"
token = trace_context.set_trace_id(trace_id)

# 3. 记录日志
logger.info("这是一条信息日志。")
logger.warning("这是一条警告日志。")

try:
    1 / 0
except Exception as e:
    logger.error("发生了一个错误。", exc_info=True)

# 4. (可选) 重置 trace_id 上下文
trace_context.reset_trace_id(token)

```

日志输出将会是类似这样的结构化文本：
```
2023-10-27 10:30:00.123 | INFO    | my_module:15 | [request-id-abc-123] | 这是一条信息日志。
2023-10-27 10:30:00.124 | WARNING | my_module:16 | [request-id-abc-123] | 这是一条警告日志。
```

## 与 FastAPI 集成

`yai-nexus-logger` 可以非常容易地与 FastAPI 集成，以实现全链路的请求追踪。

```python
# main.py
import logging
import uuid
from fastapi import FastAPI, Request
from yai_nexus_logger import LoggerBuilder, trace_context

# 在应用启动时配置 logger
logger = LoggerBuilder(name="fastapi_app", level="INFO").build()

app = FastAPI()

@app.middleware("http")
async def dispatch(request: Request, call_next):
    # 为每个请求设置唯一的 trace_id
    token = trace_context.set_trace_id(str(uuid.uuid4()))
    
    response = await call_next(request)
    
    # 在请求结束后重置 context
    trace_context.reset_trace_id(token)
    
    return response

@app.get("/")
async def read_root():
    logger.info("正在处理根路径请求。")
    return {"message": "Hello World"}

@app.get("/items/{item_id}")
async def read_item(item_id: int):
    logger.info(f"正在获取 item_id 为 {item_id} 的项目。")
    return {"item_id": item_id}
```

## 配置详解

### `LoggerBuilder(name: str, level: str = "INFO")`
创建 logger 构建器实例。
- `name`: Logger 的名称，会出现在日志记录中。
- `level`: Logger 的最低日志级别 (例如 "DEBUG", "INFO", "WARNING")。

### `.with_console_handler()`
添加一个将日志输出到控制台（`stdout`）的处理器。

### `.with_file_handler(...)`
添加一个将日志写入文件的处理器，并支持日志轮转。
- `path` (str): 日志文件的路径。默认为 `"logs/app.log"`。
- `when` (str): 日志轮转的时间单位。默认为 `"midnight"` (午夜)。
- `interval` (int): 轮转间隔。默认为 `1`。
- `backup_count` (int): 保留的备份文件数量。默认为 `30`。

### `.build()`
完成配置并返回 `logging.Logger` 实例。如果在调用 `build()` 之前没有配置任何处理器，它将默认添加一个控制台处理器。

## 开发与测试

要为此项目做贡献，请先克隆仓库并安装开发依赖：

```bash
git clone https://github.com/yai-nexus/yai-nexus-logger.git
cd yai-nexus-logger
pip install -e ".[dev]"
```

运行所有测试：
```bash
pytest
```

## 许可协议

本项目采用 [MIT 许可证](LICENSE)。
