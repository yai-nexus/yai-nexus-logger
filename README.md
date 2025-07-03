# YAI Nexus Logger

[![PyPI version](https://badge.fury.io/py/yai-nexus-logger.svg)](https://badge.fury.io/py/yai-nexus-logger)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

YAI Nexus Logger 是一个为现代 Python 应用设计的、功能强大且易于使用的日志记录工具。

想象一下，你的程序就像一个繁忙的厨房，日志就是厨房里发生所有事情的记录本。无论是谁在什么时候炒了什么菜，还是不小心打碎了一个盘子，这个记录本都会记下来。这样，当出现问题时（比如客人投诉菜咸了），你就可以翻看记录本，快速找到是哪个环节出了问题。

本工具内置了 `trace_id`（追踪ID）功能，它就像给每个订单分配一个唯一的编号。无论这个订单在厨房里经过了多少道工序，你都可以通过这个编号，追踪到它的全部过程。这在复杂的程序中非常有用！

## ✨ 核心功能

- **环境变量统一配置**：在程序启动前通过环境变量配置一次，所有地方即可开箱即用。
- **一键获取 Logger**：使用 `get_logger(__name__)` 即可获得一个继承了所有配置的 logger 实例，并能自动追踪日志来源模块。
- **结构化日志**：默认输出格式清晰的日志，方便你（和机器）阅读。
- **自动追踪ID**：自动为每一条请求链路分配 `trace_id`，让你轻松追踪程序的每一个角落。
- **与 Uvicorn 完美集成**：开箱即用，自动接管 Uvicorn 的访问日志，风格统一。
- **阿里云SLS支持**：可以直接将日志发送到阿里云日志服务，方便在云端进行日志分析和监控。
- **灵活输出**：可以同时将日志打印在控制台、保存在文件中，以及发送到云服务。

## 🚀 安装

```bash
pip install yai-nexus-logger
```

如果需要将日志发送到阿里云SLS，请安装带有`sls`依赖的扩展版本：
```bash
pip install 'yai-nexus-logger[sls]'
```

## 🎯 快速上手

下面是一个最简单的例子，展示如何快速开始使用：

```python
# main.py
from yai_nexus_logger import init_logging, get_logger

# 1. 初始化日志系统
# 在程序启动时调用一次即可，默认会配置好控制台输出
init_logging()

# 2. 获取 logger 实例
# 推荐使用 __name__ 获取实例，日志会自动包含模块路径
logger = get_logger(__name__)

# 3. 记录日志
logger.info("程序已启动")
logger.warning("这是一个警告信息")
logger.error("发生了一个错误", extra={"user_id": 123, "request_id": "abc-xyz"})
```

运行后，你会在控制台看到格式清晰的结构化日志输出。

## 🔧 配置

`yai-nexus-logger` 支持两种配置方式：环境变量（推荐用于生产环境）和代码配置（推荐用于复杂场景或测试）。

### 环境变量配置

这是最简单的方式，你只需要在启动程序前设置好相应的环境变量即可。

| 环境变量                        | 类型    | 默认值                  | 描述                                                               |
| ------------------------------- | ------- | ----------------------- | ------------------------------------------------------------------ |
| `LOG_APP_NAME`                  | `str`   | `app`                   | 应用名称，会作为日志文件名和SLS日志来源的一部分。                |
| `LOG_LEVEL`                     | `str`   | `INFO`                  | 全局日志级别 (DEBUG, INFO, WARNING, ERROR, CRITICAL)               |
| `LOG_CONSOLE_ENABLED`           | `bool`  | `true`                  | 是否启用控制台输出。                                               |
| `LOG_FILE_ENABLED`              | `bool`  | `false`                 | 是否启用文件输出。                                                 |
| `LOG_FILE_PATH`                 | `str`   | `logs/{APP_NAME}.log`   | 日志文件路径。                                                     |
| `LOG_UVICORN_INTEGRATION_ENABLED` | `bool`  | `false`                 | 是否自动接管 Uvicorn 的 access log。                               |
| `SLS_ENABLED`                   | `bool`  | `false`                 | 是否启用阿里云SLS输出。                                            |
| `SLS_ENDPOINT`                  | `str`   | -                       | 阿里云日志服务的 Endpoint (例如 `cn-hangzhou.log.aliyuncs.com`)      |
| `SLS_ACCESS_KEY_ID`             | `str`   | -                       | 阿里云 Access Key ID                                               |
| `SLS_ACCESS_KEY_SECRET`         | `str`   | -                       | 阿里云 Access Key Secret                                           |
| `SLS_PROJECT`                   | `str`   | -                       | 阿里云日志项目名称。                                               |
| `SLS_LOGSTORE`                  | `str`   | -                       | 阿里云日志库名称。                                                 |
| `SLS_TOPIC`                     | `str`   | `default`               | 日志主题。                                                         |

### 代码配置

如果需要更灵活的配置，你可以使用 `LoggerConfigurator`。

```python
from yai_nexus_logger import LoggerConfigurator, init_logging, get_logger

# 使用建造者模式进行链式配置
config = (
    LoggerConfigurator(app_name="my-awesome-app", level="DEBUG")
    .with_console_handler()  # 添加控制台输出
    .with_file_handler(log_path="logs/my_app.log")  # 添加文件输出
    .with_uvicorn_integration() # 开启 Uvicorn 集成
)

# 使用配置初始化日志系统
init_logging(config)

logger = get_logger(__name__)
logger.info("日志系统已通过代码配置完成！")
```

## 🧩 集成示例

### 与 FastAPI / Uvicorn 集成

为了在 FastAPI 应用中实现全链路的 `trace_id` 追踪，并统一 `access log` 格式，请遵循以下步骤：

1.  **开启 Uvicorn 集成**: 设置环境变量 `LOG_UVICORN_INTEGRATION_ENABLED=true` 或在代码中调用 `.with_uvicorn_integration()`。
2.  **添加中间件**: 在 FastAPI 应用中添加一个中间件来生成和管理 `trace_id`。

```python
# fastapi_app.py
import uuid
from fastapi import FastAPI, Request, Response
from yai_nexus_logger import get_logger, init_logging, trace_context

# 1. 在应用启动前初始化日志
# 假设已设置 LOG_UVICORN_INTEGRATION_ENABLED=true
init_logging()

app = FastAPI()
logger = get_logger(__name__)

# 2. 添加中间件以注入 trace_id
@app.middleware("http")
async def trace_id_middleware(request: Request, call_next):
    # 尝试从请求头获取 trace_id，否则生成一个新的
    trace_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
    
    # 将 trace_id 存入上下文
    token = trace_context.set_trace_id(trace_id)

    response = await call_next(request)
    
    # 在响应头中返回 trace_id
    response.headers["X-Request-ID"] = trace_id
    
    # 清理上下文
    trace_context.reset_trace_id(token)
    return response

@app.get("/")
async def root():
    logger.info("Hello from the root endpoint!")
    return {"message": "Check your logs and response headers for X-Request-ID."}

# 3. 启动应用
# uvicorn fastapi_app:app --reload
```

现在，当你访问 Uvicorn 服务时，它的访问日志会自动变成结构化的 JSON 格式，并且包含 `trace_id`。你应用内的所有日志也会自动附带相同的 `trace_id`。

### 与阿里云 SLS 集成

1.  **安装依赖**: `pip install 'yai-nexus-logger[sls]'`
2.  **配置环境变量**: 设置好 `SLS_ENABLED=true` 以及其他 `SLS_*` 相关变量。
3.  **初始化日志**: `init_logging()`

完成以上步骤后，所有日志将自动被发送到你指定的阿里云日志项目中。

## 🧑‍💻 本地开发

我们欢迎任何形式的贡献！请遵循以下步骤进行本地开发：

1.  **克隆仓库**
    ```bash
    git clone https://github.com/yai-nexus/yai-nexus-logger.git
    cd yai-nexus-logger
    ```

2.  **创建并激活虚拟环境**
    ```bash
    python -m venv venv
    source venv/bin/activate  # macOS/Linux
    # venv\Scripts\activate  # Windows
    ```

3.  **安装开发依赖**
    ```bash
    pip install -e '.[dev,sls]'
    ```
    这会以可编辑模式安装包，并包含所有测试和代码风格检查所需的依赖。

4.  **运行测试**
    ```bash
    pytest
    ```

## 📜 License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.
