"""Internal formatter for the logger, handles trace_id and log record formatting."""

import logging

from yai_nexus_logger.trace_context import trace_context
from .internal_utils import extract_extra_fields


class InternalFormatter(logging.Formatter):
    """
    自定义日志格式化程序，主要功能：
    1. 在日志记录中自动添加 trace_id。
    2. 缩写模块名称，使日志更紧凑。
    3. 对错误级别以上的日志自动附加堆栈跟踪信息。
    """

    def __init__(self, fmt: str | None = None, datefmt: str | None = None):
        super().__init__(fmt, datefmt or "%Y-%m-%d %H:%M:%S")

    def _abbreviate_module_name(self, module_name: str) -> str:
        """
        将模块名缩写，例如：
        'src.app.routers.items' -> 's.a.r.items'
        """
        if "." not in module_name:
            return module_name

        parts = module_name.split(".")
        # 如果路径少于4段，则不缩写
        if len(parts) <= 3:
            return module_name

        # 缩写前几个部分，保留最后一部分
        abbreviated_parts = [p[0] if p.isalpha() else p for p in parts[:-1]]
        return ".".join(abbreviated_parts) + "." + parts[-1]

    def format(self, record: logging.LogRecord) -> str:
        # 注入 trace_id
        record.trace_id = trace_context.get_trace_id() or "No-Trace-ID"

        # 缩写模块名
        record.module = self._abbreviate_module_name(record.module)

        # 为错误日志添加堆栈信息
        if record.levelno >= logging.ERROR and record.exc_info:
            record.exc_text = self.formatException(record.exc_info)

        # 处理 extra 参数
        formatted_message = super().format(record)
        
        # 检查是否有 extra 字段需要添加
        extra_fields = extract_extra_fields(record)
        if extra_fields:
            extra_str = " | ".join([f"{k}={v}" for k, v in extra_fields.items()])
            formatted_message += f" | {extra_str}"
        
        return formatted_message

