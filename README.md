# YAI Nexus Logger

[![PyPI version](https://badge.fury.io/py/yai-nexus-logger.svg)](https://badge.fury.io/py/yai-nexus-logger)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

YAI Nexus Logger 是一个为现代 Python 应用设计的、功能强大且易于使用的日志记录工具。

想象一下，你的程序就像一个繁忙的厨房，日志就是厨房里发生所有事情的记录本。无论是谁在什么时候炒了什么菜，还是不小心打碎了一个盘子，这个记录本都会记下来。这样，当出现问题时（比如客人投诉菜咸了），你就可以翻看记录本，快速找到是哪个环节出了问题。

本工具内置了 `trace_id`（追踪ID）功能，它就像给每个订单分配一个唯一的编号。无论这个订单在厨房里经过了多少道工序，你都可以通过这个编号，追踪到它的全部过程。这在复杂的程序中非常有用！

## 🤔 为什么要使用日志记录器？

你可能会想："我用 `print()` 也能输出信息，为什么还需要一个日志记录器呢？"

`print()` 很方便，但在真实的项目中，它有几个缺点：
- **信息混乱**：所有信息（调试、警告、错误）都混在一起，难以区分。
- **无法分级**：你无法方便地只看"紧急错误"，而忽略"普通信息"。
- **难以管理**：当程序变得复杂，你很难控制在什么时候、什么地方打印信息。
- **输出位置单一**：`print()` 只能输出到控制台，而日志记录器可以同时输出到控制台、文件，甚至发送到远程服务器。

`yai-nexus-logger` 解决了以上所有问题，它为你提供了一个专业的"记录本"，让你的程序信息井井有条。

## ✨ 核心功能

- **一键配置**：像搭积木一样，用 `LoggerBuilder` 轻松配置出你想要的日志记录器。
- **结构化日志**：默认输出格式清晰的日志，方便你（和机器）阅读。
- **自动追踪ID**：自动为每一条请求链路分配 `trace_id`，让你轻松追踪程序的每一个角落。
- **日志自动分割**：当日志文件太大的时候，会自动按时间分割，防止一个文件无限变大。
- **与 Uvicorn 完美集成**：开箱即用，自动接管 Uvicorn 的访问日志，风格统一。
- **灵活输出**：可以同时将日志打印在控制台和保存在文件中。

## 🚀 安装

```bash
pip install yai-nexus-logger
```

## 💡 快速上手

下面是一个简单的例子，教你如何配置和使用。

```python
import logging
from yai_nexus_logger import LoggerBuilder, trace_context

# 1. 使用 LoggerBuilder 像搭积木一样构建 logger
#    可以指定一个名字和日志的"重要等级"
logger = LoggerBuilder(name="my_app", level="DEBUG") \
    .with_console_handler() \
    .with_file_handler(path="logs/my_app.log") \
    .build()

# 2. (可选) 如果你需要追踪一个特定的任务，可以给它设置一个追踪ID
trace_id = "request-id-abc-123"
token = trace_context.set_trace_id(trace_id)

# 3. 记录不同类型的日志
logger.info("这是一条普通信息，比如：'用户小明登录了'。")
logger.warning("这是一条警告，比如：'磁盘空间快满了'。")

try:
    1 / 0
except Exception as e:
    # exc_info=True 会把错误的详细信息也记录下来
    logger.error("发生了一个严重错误！", exc_info=True)

# 4. (可选) 任务完成，清除追踪ID
trace_context.reset_trace_id(token)

```

日志输出会是下面这样，格式非常清晰：
```
2023-10-27 10:30:00.123 | INFO    | my_module:15 | [request-id-abc-123] | 这是一条普通信息，比如：'用户小明登录了'。
2023-10-27 10:30:00.124 | WARNING | my_module:16 | [request-id-abc-123] | 这是一条警告，比如：'磁盘空间快满了'。
```

## 🌐 与 FastAPI 和 Uvicorn 集成

在 FastAPI 这样的 Web 框架中，`trace_id` 特别有用。它可以把一个用户的单次请求（从访问网站到返回结果）的所有相关日志都串起来。

`yai-nexus-logger` 提供了与 Uvicorn 的无缝集成。你只需要在构建 logger 时调用 `.with_uvicorn_integration()`，它就会自动接管 Uvicorn 的所有日志（包括访问日志），并使用我们统一的格式进行输出。

```python
# main.py
import logging
import uuid
from fastapi import FastAPI, Request
from yai_nexus_logger import LoggerBuilder, trace_context

# 在应用启动时配置好 logger，并启用 Uvicorn 集成
logger = (
    LoggerBuilder(name="fastapi_app", level="INFO")
    .with_uvicorn_integration()
    .build()
)

app = FastAPI()

# 这里我们使用 "中间件" (middleware)，它像一个门卫
# 每个请求进来时，门卫都会给它分配一个唯一的追踪ID
@app.middleware("http")
async def dispatch(request: Request, call_next):
    # 为每个请求设置唯一的 trace_id
    token = trace_context.set_trace_id(str(uuid.uuid4()))

    response = await call_next(request)

    # 请求结束后，清除这个ID
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

现在，当你使用 Uvicorn 运行你的应用时，无论是你自己的应用日志，还是 Uvicorn 的访问日志，都会包含 `trace_id` 并被输出到你配置的控制台或文件中，格式完全统一！

## ⚙️ 配置详解

### `LoggerBuilder(name: str, level: str = "INFO")`
创建 logger 构建器实例。
- `name`: 你的 logger 的名字，会显示在日志里。
- `level`: 日志的最低"重要等级"，只有等于或高于这个等级的日志才会被记录。("DEBUG", "INFO", "WARNING", "ERROR")。

### `.with_console_handler()`
添加一个"控制台输出器"，让日志显示在你的程序运行窗口。

### `.with_file_handler(...)`
添加一个"文件输出器"，把日志保存到文件里。
- `path` (str): 日志文件的路径，比如 `"logs/app.log"`。
- `when` (str): 日志文件分割的时间单位。比如 `"midnight"` (每天半夜)。
- `interval` (int): 分割间隔。
- `backup_count` (int): 保留多少个旧的日志文件。

### `.with_uvicorn_integration()`
启用与 Uvicorn 的集成。
调用此方法后，Uvicorn 的所有日志将被重定向到此 logger 配置的处理器，
并且访问日志会自动包含 trace_id。

### `.build()`
完成所有配置，返回一个可以使用的 `logging.Logger` 实例。如果你没有配置任何输出器，它会默认帮你配置一个"控制台输出器"。

## 🛠️ 开发与测试

想为这个项目贡献代码吗？太棒了！请按照以下步骤操作：

```bash
git clone https://github.com/yai-nexus/yai-nexus-logger.git
cd yai-nexus-logger

# 推荐使用 uv 创建虚拟环境
uv venv
source .venv/bin/activate

# 安装开发依赖
uv pip install -e ".[dev]"
```

运行所有测试：
```bash
pytest
```

## 📄 许可协议

本项目采用 [MIT 许可证](LICENSE)。
