# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

YAI Nexus Logger is a structured logging library for Python applications with built-in trace_id support. The project is written entirely in Chinese (comments, docstrings, variable names) and focuses on providing unified logging configuration through environment variables and seamless integration with FastAPI/Uvicorn applications.

## Development Commands

### Testing
```bash
# Run all tests with coverage
pytest

# Run tests with coverage report
pytest --cov=src/yai_nexus_logger --cov-report=term-missing

# Run specific test
pytest tests/yai_nexus_logger/unit/test_trace_context.py
```

### Code Quality
```bash
# Lint and format code
ruff check src/ tests/ examples/
ruff format src/ tests/ examples/

# Fix auto-fixable issues
ruff check --fix src/ tests/ examples/
```

### Installation for Development
```bash
# Install in editable mode with all dependencies
pip install -e '.[dev,sls]'
```

## Architecture

### Core Components
- **core.py**: Main entry points (`init_logging()`, `get_logger()`)
- **configurator.py**: Builder pattern for logger configuration (`LoggerConfigurator`)
- **trace_context.py**: Context management for trace_id tracking using ContextVar
- **uvicorn_support.py**: Integration layer for Uvicorn access logs

### Internal Modules (`src/yai_nexus_logger/internal/`)
- **internal_formatter.py**: Custom JSON formatter with trace_id injection
- **internal_handlers.py**: Console and file handler factories
- **internal_settings.py**: Environment variable configuration management
- **internal_sls_handler.py**: Alibaba Cloud SLS (Simple Log Service) integration

### Key Design Patterns
1. **Builder Pattern**: `LoggerConfigurator` uses fluent API for configuration
2. **Settings Pattern**: Environment variables centralized in `internal_settings.py`
3. **Context Variables**: `trace_context` uses Python's ContextVar for async-safe trace_id management
4. **Factory Pattern**: Handler creation abstracted through factory functions

### Trace ID System
The library uses Python's `contextvars.ContextVar` to maintain trace_id across async boundaries. This is critical for request tracing in FastAPI applications. The trace_id is automatically injected into all log records through the custom formatter.

### Environment Variable Configuration
All configuration is driven by environment variables with the `LOG_` or `SLS_` prefix. This follows 12-factor app principles and makes the library suitable for containerized deployments.

## Testing Strategy

### Test Structure
- **Unit tests**: `tests/yai_nexus_logger/unit/` - Test individual components in isolation
- **Integration tests**: `tests/yai_nexus_logger/integration/` - Test component interactions
- **Example tests**: `tests/examples/` - Test example code functionality

### Test Coverage
The project maintains high test coverage with pytest-cov. All new features should include comprehensive tests covering both success and error scenarios.

## Language and Localization

**Important**: This codebase is entirely in Chinese, including:
- All comments and docstrings
- Variable names (where semantically meaningful)
- Error messages and log output
- README and documentation

When contributing, maintain consistency with the Chinese naming and documentation patterns.

## Integration Points

### FastAPI/Uvicorn
The library provides seamless integration with FastAPI through:
1. Automatic Uvicorn access log formatting
2. Middleware for trace_id injection
3. Unified log output format across application and access logs

### Alibaba Cloud SLS
Optional integration with Alibaba Cloud's Simple Log Service for centralized logging in cloud deployments.