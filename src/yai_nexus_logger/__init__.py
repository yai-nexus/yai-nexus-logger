# src/yai_nexus_logger/__init__.py

"""
YAI Nexus Logger.

一个为现代 Python 应用设计的、功能强大且易于使用的日志记录工具。
"""

__version__ = "0.2.0"

# 从 .logger_builder 模块导入 LoggerBuilder 和新的 get_logger 函数
from .logger_builder import LoggerBuilder, get_logger
# 从 .trace_context 模块导入 trace_context，用于追踪ID
from .trace_context import trace_context

# 定义对外暴露的公共接口
__all__ = ["LoggerBuilder", "get_logger", "trace_context"]