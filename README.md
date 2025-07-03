# YAI Nexus Logger

A powerful, structured logger for modern Python applications, with built-in `trace_id` support for easy request tracking, especially in asynchronous frameworks like FastAPI.

## Features

- **Trace ID Injection**: Automatically injects a unique `trace_id` into every log record for easy cross-service request tracing.
- **Structured Logging**: Logs are formatted in a clean, readable, and structured way.
- **Uvicorn Integration**: Provides a ready-to-use configuration for `uvicorn` to unify application and server logs.
- **Asynchronous Ready**: Uses `contextvars` to safely manage `trace_id` in concurrent environments.
- **Automatic Exception Tracking**: Automatically logs tracebacks for errors.
- **File Rotation**: Supports time-based log file rotation.

## Installation

You can install the library using pip:

```bash
pip install yai-nexus-logger
```
*(Note: This package is not yet published to PyPI. This is a placeholder.)*

For development, clone the repository and install in editable mode:
```bash
git clone https://github.com/your-username/yai-nexus-logger.git
cd yai-nexus-logger
pip install -e .[dev] 
```
*(You would need to define `[dev]` extras in `pyproject.toml` containing `fastapi`, `uvicorn`, etc.)*

## Quick Start

Here's how to use `yai-nexus-logger` in a FastAPI application.

### 1. The Application (`main.py`)

```python
import logging
from time import time
from typing import Callable

import uvicorn
from fastapi import FastAPI, Request, Response

# Import the necessary components from our logger library
from yai_nexus_logger import (
    get_trace_id, 
    reset_trace_id, 
    set_trace_id, 
    setup_logger, 
    get_uvicorn_log_config
)

# Initialize the logger
# This can be done once at application startup.
logger = setup_logger(name="my-fastapi-app", level="DEBUG")

app = FastAPI()

@app.middleware("http")
async def logging_middleware(request: Request, call_next: Callable) -> Response:
    """
    Middleware to inject and manage the trace_id for each request.
    """
    trace_id = request.headers.get("X-Trace-ID") or get_trace_id()
    token = set_trace_id(trace_id)
    
    start_time = time()
    
    try:
        response = await call_next(request)
        response.headers["X-Trace-ID"] = get_trace_id()
        status_code = response.status_code
    except Exception:
        logger.exception("Unhandled exception during request processing")
        status_code = 500
        response = Response(status_code=status_code)
    finally:
        process_time = (time() - start_time) * 1000
        logger.info(
            f'"{request.method} {request.url.path}" {status_code} {process_time:.2f}ms'
        )
        reset_trace_id(token)

    return response

@app.get("/")
async def read_root():
    logger.info("Handling request for the root endpoint.")
    return {"message": "Hello from yai-nexus-logger!"}

@app.get("/error")
async def trigger_error():
    try:
        raise ValueError("This is a test error.")
    except ValueError:
        logger.error("Caught an expected ValueError.", exc_info=True)
    return {"message": "Error endpoint triggered and logged."}


if __name__ == "__main__":
    # Use the provided Uvicorn log configuration
    log_config = get_uvicorn_log_config(level="INFO")
    
    uvicorn.run(
        "__main__:app", # Use "__main__:app" to run directly
        host="127.0.0.1",
        port=8000,
        reload=True,
        log_config=log_config,
    )
```

### 2. Run the App

Save the code above as `main.py`, install the dependencies, and run it:

```bash
pip install fastapi "uvicorn[standard]"
python main.py
```

### 3. See the Logs

- **Console**: You will see structured logs in your terminal.
- **File**: A `logs/` directory will be created with a rotating `app.log` file.

Send some requests to see it in action:
```bash
# Basic request
curl http://127.0.0.1:8000/

# Request with a custom trace ID
curl -H "X-Trace-ID: my-special-request-123" http://127.0.0.1:8000/

# Request that triggers an error
curl http://127.0.0.1:8000/error
```

You will see the `trace_id` reflected in the corresponding log entries.