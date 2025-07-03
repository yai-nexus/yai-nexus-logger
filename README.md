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

基础安装：
```bash
pip install yai-nexus-logger
```

如果需要使用阿里云SLS（日志服务）支持：
```bash
pip install 'yai-nexus-logger[sls]'
```

## 💡 核心用法：通过 `get_logger` 统一配置

这是使用本组件 **最核心且推荐** 的方式。你不再需要在代码中编写复杂的配置，而是通过环境变量来完成。

### 1. 配置环境变量

在启动你的应用前，根据需要设置以下环境变量。

**基础配置:**
- `LOG_APP_NAME`: 你的应用名称 (默认: `app`)。**这个名称很重要，它将作为所有日志记录器的"根"。**
- `LOG_LEVEL`: 日志级别，如 "INFO", "DEBUG" (默认: `INFO`)

**输出到文件 (可选):**
- `LOG_FILE_ENABLED`: 设置为 `true` 来启用文件日志。
- `LOG_FILE_PATH`: 日志文件路径 (默认: `logs/<LOG_APP_NAME>.log`)

**集成 Uvicorn (可选, 用于 FastAPI 等):**
- `LOG_UVICORN_INTEGRATION_ENABLED`: 设置为 `true` 来自动接管 Uvicorn 日志。

**输出到阿里云 SLS (可选):**
- `SLS_ENABLED`: 设置为 `true` 来启用 SLS 日志。
- `SLS_ENDPOINT`: 你的SLS地域节点。
- `SLS_ACCESS_KEY_ID`: 你的AccessKey ID。
- `SLS_ACCESS_KEY_SECRET`: 你的AccessKey Secret。
- `SLS_PROJECT`: 你的项目名。
- `SLS_LOGSTORE`: 你的日志库名。
- `SLS_TOPIC`: (可选) 日志主题。
- `SLS_SOURCE`: (可选) 日志来源。


### 2. 在代码中使用

你的代码会变得极其简单。只需要一行，就可以获得一个功能完备的 logger。

```python
# my_module.py
from yai_nexus_logger import get_logger, trace_context

# 强烈推荐使用 __name__ 作为 logger 名称。
# 这会自动创建名为 '你的应用名.my_module' 的 logger，
# 它继承了所有配置，并且日志输出时能清晰地看到来源。
logger = get_logger(__name__)

# (可选) 如果你需要追踪一个特定的任务，可以给它设置一个追踪ID
token = trace_context.set_trace_id("request-abc-123")

# 记录不同类型的日志
logger.info("这是一条普通信息，比如：'用户小明登录了'。")
logger.warning("这是一条警告，比如：'磁盘空间快满了'。")

try:
    1 / 0
except Exception as e:
    # exc_info=True 会把错误的详细信息也记录下来
    logger.error("发生了一个严重错误！", exc_info=True)

# (可选) 任务完成，清除追踪ID
trace_context.reset_trace_id(token)
```
就这样！`get_logger` 会自动读取所有环境变量，并在第一次被调用时完成对根记录器（由`LOG_APP_NAME`定义）的所有复杂配置工作。之后你从任何模块中获取的 logger 都会成为它的"孩子"，自动享受到所有配置好的功能。

## 🌐 与 FastAPI 和 Uvicorn 集成

在 FastAPI 中使用 `get_logger` 会让你的代码非常整洁。

### 1. 配置环境变量

假设我们希望将 FastAPI 的日志同时输出到控制台和文件，并接管 Uvicorn 的访问日志。

```bash
# 在你的启动脚本或环境中设置这些变量
export LOG_APP_NAME="fastapi_app"
export LOG_LEVEL="INFO"
export LOG_FILE_ENABLED="true"
export LOG_UVICORN_INTEGRATION_ENABLED="true"
```

### 2. 应用代码

```python
# main.py
import uuid
from fastapi import FastAPI, Request
from yai_nexus_logger import get_logger, trace_context

# 只需这一行，所有配置都会自动应用
# 在 main.py 中，__name__ 会是 "main"，所以 logger 名为 "fastapi_app.main"
logger = get_logger(__name__)

app = FastAPI()

# 中间件，为每个请求自动添加 trace_id
@app.middleware("http")
async def dispatch(request: Request, call_next):
    token = trace_context.set_trace_id(str(uuid.uuid4()))
    response = await call_next(request)
    trace_context.reset_trace_id(token)
    return response

@app.get("/")
async def read_root():
    logger.info("正在处理根路径请求。")
    return {"message": "Hello World"}
```
现在，用 Uvicorn 运行应用，所有的日志（你自己的应用日志和 Uvicorn 的访问日志）都会按你的配置输出，并且带有 `trace_id`。

## 🔗 与阿里云SLS集成

将日志发送到阿里云SLS也同样简单。代码和普通用法完全一样！

### 1. 配置环境变量

```bash
# 应用基础配置
export LOG_APP_NAME="my_sls_app"
export LOG_LEVEL="INFO"

# 启用SLS
export SLS_ENABLED="true"

# SLS 的详细认证信息
export SLS_ENDPOINT="cn-hangzhou.log.aliyuncs.com"
export SLS_ACCESS_KEY_ID="你的AccessKey ID"
export SLS_ACCESS_KEY_SECRET="你的AccessKey Secret"
export SLS_PROJECT="你的项目名"
export SLS_LOGSTORE="你的日志库名"
export SLS_TOPIC="my_python_app" # 可选
```

### 2. 应用代码

```python
from yai_nexus_logger import get_logger

# logger 名为 "my_sls_app.some_module"
logger = get_logger("some_module")

logger.info("应用启动成功")
logger.warning("内存使用率较高")
logger.error("数据库连接失败")
```
这些日志现在会自动发送到你配置的阿里云SLS项目中。

## ⚙️ 高级用法：手动构建

如果你需要在代码中进行更精细的动态控制，或者无法使用环境变量，你依然可以使用 `LoggerConfigurator` 来手动构建 logger。**请注意，这种方式会覆盖基于环境变量的自动配置。**

from yai_nexus_logger import LoggerConfigurator, init_logging, get_logger

# 1. 使用 LoggerConfigurator 手动配置
# 注意：配置器不再需要 `name`，它会自动从环境变量 LOG_APP_NAME 或默认值 "app" 获取
# 你可以在这里设置环境变量，来影响下面的配置
# os.environ["LOG_APP_NAME"] = "manual_app"

configurator = (
    LoggerConfigurator(level="DEBUG")
    .with_console_handler()
    .with_file_handler() # 默认路径是 logs/manual_app.log (取决于 LOG_APP_NAME)
)

# 2. 调用 init_logging 应用配置
init_logging(configurator)

# 3. 在应用的任何地方获取 logger
# get_logger() 会获取到名为 "manual_app" 的根 logger
logger = get_logger()

logger.debug("这是一个手动配置的 debug 信息。")
logger.info("这个 logger 继承了手动配置。")

# 你也可以获取子 logger
db_logger = get_logger("database")
db_logger.info("正在连接数据库...")

## 贡献

欢迎任何形式的贡献！无论是提交 issue、发起 pull request 还是提供建议，我们都非常欢迎。

在提交代码前，请确保：
- 代码遵循 PEP 8 风格指南。
- 相关的测试用例已添加并通过。

## License
[MIT](LICENSE)
