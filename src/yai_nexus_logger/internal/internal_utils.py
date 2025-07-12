"""内部工具函数模块"""

import logging


def extract_extra_fields(record: logging.LogRecord) -> dict:
    """
    从 LogRecord 中提取 extra 字段。
    排除标准的 logging 属性和我们自定义的属性。
    
    Args:
        record: logging.LogRecord 实例
        
    Returns:
        dict: 包含所有 extra 字段的字典
    """
    # 标准 logging 属性
    standard_attrs = {
        'name', 'msg', 'args', 'levelname', 'levelno', 'pathname', 'filename',
        'module', 'lineno', 'funcName', 'created', 'msecs', 'relativeCreated',
        'thread', 'threadName', 'processName', 'process', 'getMessage', 'exc_info',
        'exc_text', 'stack_info', 'message', 'asctime', 'taskName'
    }
    
    # 我们自定义的属性
    custom_attrs = {'trace_id'}
    
    # 提取 extra 字段
    extra_fields = {}
    for key, value in record.__dict__.items():
        if key not in standard_attrs and key not in custom_attrs:
            extra_fields[key] = value
    
    return extra_fields