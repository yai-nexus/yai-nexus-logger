import logging
import os
import shutil
import uuid

from src.yai_nexus_logger.logger import setup_logger
from src.yai_nexus_logger.handler import LOG_DIR

def get_unique_name() -> str:
    return f"test_logger_{uuid.uuid4().hex}"

def cleanup_logs():
    """测试后清理日志目录"""
    if os.path.exists(LOG_DIR):
        shutil.rmtree(LOG_DIR)


def test_setup_logger_creates_logger_with_correct_config():
    """
    测试 setup_logger 是否能创建一个具有正确名称和级别的 logger。
    """
    logger_name = get_unique_name()
    logger = setup_logger(name=logger_name, level="DEBUG")
    
    assert logger.name == logger_name
    assert logger.level == logging.DEBUG
    assert len(logger.handlers) == 2  # Console and File handlers
    assert not logger.propagate
    
    cleanup_logs()


def test_setup_logger_avoids_duplicate_handlers():
    """
    测试重复调用 setup_logger 是否会添加重复的处理器。
    """
    logger_name = get_unique_name()
    
    # 第一次调用
    logger = setup_logger(name=logger_name, level="INFO")
    assert len(logger.handlers) == 2
    
    # 第二次调用
    logger_same = setup_logger(name=logger_name, level="INFO")
    assert len(logger_same.handlers) == 2  # 处理器数量不应增加
    
    cleanup_logs()


def test_log_file_creation():
    """
    测试调用 setup_logger 后是否会创建日志目录。
    """
    logger_name = get_unique_name()
    logger = setup_logger(name=logger_name, level="INFO")
    
    # 写入一条日志以确保文件被创建
    logger.info("creating log file for test")
    
    log_file = LOG_DIR / "app.log"
    
    assert os.path.isdir(LOG_DIR)
    assert os.path.isfile(log_file)
    
    cleanup_logs() 