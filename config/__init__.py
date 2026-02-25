# config/__init__.py
"""
配置包初始化文件
"""

from .display import SCREEN_WIDTH, SCREEN_HEIGHT, FPS
from .game import (
    TITLE,
    DEFAULT_TOTAL_QUESTIONS,
    DEFAULT_START_LEVEL,
    MIN_LEVEL,
    MAX_LEVEL,
    MIN_QUESTIONS,
    MAX_QUESTIONS
)
from .levels import E_SIZE_LEVELS