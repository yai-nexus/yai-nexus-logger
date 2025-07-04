# src/yai_nexus_logger/__init__.py

"""
YAI Nexus Logger.

一个为现代 Python 应用设计的、功能强大且易于使用的日志记录工具。
"""

__version__ = "0.2.0"

# 从 .configurator 模块导入 LoggerConfigurator 类
from .configurator import LoggerConfigurator

# 从 .core 模块导入核心函数
from .core import get_logger, init_logging

# 从 .trace_context 模块导入 trace_context，用于追踪ID
from .trace_context import trace_context

# 定义对外暴露的公共接口
__all__ = [
    "LoggerConfigurator",
    "get_logger",
    "init_logging",
    "trace_context",
]
