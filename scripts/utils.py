#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
通用工具函数 - 图片光线迁移项目
"""

import sys
import time
import logging
import functools
from pathlib import Path
from typing import Callable, Any, Dict, List

logger = logging.getLogger(__name__)

def retry(max_attempts: int = 3, delay: float = 5.0, backoff: float = 2.0, exceptions: tuple = (Exception,)):
    """
    重试装饰器

    Args:
        max_attempts: 最大重试次数（含初次）
        delay: 初始延迟（秒）
        backoff: 退避系数
        exceptions: 要捕获的异常类型
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            attempts = 0
            current_delay = delay

            while attempts < max_attempts:
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    attempts += 1
                    if attempts >= max_attempts:
                        logger.error(f"[ERR] 重试耗尽 ({max_attempts}次), 最后错误: {e}")
                        raise

                    logger.warning(f"[WARN]  第 {attempts} 次重试，延迟 {current_delay}s 后重试: {e}")
                    time.sleep(current_delay)
                    current_delay *= backoff

        return wrapper
    return decorator

def ensure_dir(path: str or Path) -> Path:
    """
    确保目录存在，不存在则创建

    Args:
        path: 目录路径

    Returns:
        Path 对象
    """
    p = Path(path)
    p.mkdir(parents=True, exist_ok=True)
    return p

def load_config(config_path: str = "config.yaml") -> Dict[str, Any]:
    """
    加载 YAML 配置文件

    Args:
        config_path: 配置文件路径

    Returns:
        配置字典
    """
    import yaml

    config_file = Path(config_path)
    if not config_file.exists():
        raise FileNotFoundError(f"配置文件不存在: {config_path}")

    with open(config_file, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)

    logger.info(f"[OK] 配置已加载: {config_path}")
    return config

def setup_project_logging(log_dir: str = "logs", level: str = "INFO", log_to_file: bool = True):
    """
    配置项目全局日志

    Args:
        log_dir: 日志目录
        level: 日志级别
        log_to_file: 是否写入文件
    """
    import datetime

    log_level = getattr(logging, level.upper(), logging.INFO)

    handlers = [logging.StreamHandler(sys.stdout)]
    if log_to_file:
        ensure_dir(log_dir)
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        log_file = Path(log_dir) / f"project_{timestamp}.log"
        handlers.append(logging.FileHandler(log_file, encoding='utf-8'))

    logging.basicConfig(
        level=log_level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        handlers=handlers
    )

    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("agent-browser").setLevel(logging.WARNING)

    logger.info("日志系统初始化完成")

def flatten_list(nested_list: List[List]) -> List:
    """
    扁平化嵌套列表

    Example:
        [[a, b], [c]] → [a, b, c]
    """
    return [item for sublist in nested_list for item in sublist]

def chunked_list(lst: List, chunk_size: int) -> List[List]:
    """
    将列表分块

    Args:
        lst: 原始列表
        chunk_size: 块大小

    Returns:
        分块后的列表的列表
    """
    return [lst[i:i + chunk_size] for i in range(0, len(lst), chunk_size)]

def format_duration(seconds: float) -> str:
    """
    格式化时长（秒 → 时:分:秒）

    Args:
        seconds: 秒数

    Returns:
        格式化字符串
    """
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)

    if hours > 0:
        return f"{hours}h {minutes}m {secs}s"
    elif minutes > 0:
        return f"{minutes}m {secs}s"
    else:
        return f"{secs}s"

def calculate_eta(start_time: float, current: int, total: int) -> str:
    """
    计算预计剩余时间

    Args:
        start_time: 开始时间戳
        current: 当前进度
        total: 总任务数

    Returns:
        ETA 字符串
    """
    if current == 0:
        return "N/A"

    elapsed = time.time() - start_time
    rate = elapsed / current
    remaining = (total - current) * rate

    return format_duration(remaining)

def safe_filename(name: str) -> str:
    """
    清理文件名，移除非法字符

    Args:
        name: 原始文件名

    Returns:
        安全的文件名
    """
    import re

    # 移除 Windows/Linux 非法字符
    name = re.sub(r'[<>:"/\\|?*]', '_', name)

    # 移除多余空格和点
    name = name.strip('. ')

    # 限制长度
    if len(name) > 200:
        name = name[:200]

    return name

# 测试代码
if __name__ == "__main__":
    setup_project_logging(level="DEBUG")

    # 测试 retry
    @retry(max_attempts=3, delay=1)
    def test_func(should_fail: bool = True):
        if should_fail:
            raise ValueError("test error")
        return "success"

    try:
        result = test_func(should_fail=False)
        print(f"Test result: {result}")
    except Exception as e:
        print(f"Test failed after retries: {e}")

    # 测试其他工具
    print(f"Format duration: {format_duration(3665)}")  # 1h 1m 5s
    print(f"Safe filename: {safe_filename('阿霞/百叶窗?.jpg')}")
