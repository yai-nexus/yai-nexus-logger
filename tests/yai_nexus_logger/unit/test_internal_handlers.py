# tests/yai_nexus_logger/unit/test_internal_handlers.py

import logging
from pathlib import Path

from yai_nexus_logger.internal.internal_handlers import (
    get_console_handler,
    get_file_handler,
)

# 获取一个标准的 formatter，用于测试
formatter = logging.Formatter("%(message)s")


def test_get_console_handler(capsys):
    """测试 get_console_handler 能否正确创建并格式化日志。"""
    handler = get_console_handler(formatter)
    logger = logging.getLogger("test_console")
    logger.setLevel(logging.INFO)
    logger.handlers = [handler]

    test_message = "Hello, Console!"
    logger.info(test_message)

    captured = capsys.readouterr()
    assert test_message in captured.out


def test_get_file_handler(tmp_path: Path):
    """测试 get_file_handler 能否在指定路径创建日志文件并写入内容。"""
    log_file = tmp_path / "test.log"
    handler = get_file_handler(
        formatter=formatter,
        path=str(log_file),
        when="D",
        interval=1,
        backup_count=1,
    )
    logger = logging.getLogger("test_file")
    logger.setLevel(logging.INFO)
    logger.handlers = [handler]

    test_message = "Hello, File!"
    logger.info(test_message)
    handler.close()  # 关闭 handler 以确保内容写入文件

    assert log_file.exists()
    assert test_message in log_file.read_text()
