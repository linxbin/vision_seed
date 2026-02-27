import os
import pygame
from typing import Dict, Any, List


def _project_root() -> str:
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def run_startup_health_check() -> Dict[str, Any]:
    """启动健康检查：资源缺失仅告警，不阻断启动。"""
    root = _project_root()
    assets_dir = os.path.join(root, "assets")

    checks = {
        "correct_sound": os.path.exists(os.path.join(assets_dir, "correct.wav")),
        "wrong_sound": os.path.exists(os.path.join(assets_dir, "wrong.wav")),
        "chinese_font": os.path.exists(os.path.join(assets_dir, "SimHei.ttf")),
    }

    warnings: List[str] = []
    if not checks["correct_sound"] or not checks["wrong_sound"]:
        warnings.append("Sound assets missing. Audio feedback will be degraded.")
    if not checks["chinese_font"]:
        warnings.append("Chinese font missing (assets/SimHei.ttf). Chinese text may fallback to system font.")

    for warning in warnings:
        print(f"[startup-check] {warning}")

    return {"checks": checks, "warnings": warnings}


def safe_init_audio() -> bool:
    """安全初始化音频。失败时降级运行，不抛异常。"""
    try:
        pygame.mixer.init(frequency=22050, size=-16, channels=2, buffer=512)
        return True
    except Exception as e:
        print(f"[startup-check] Audio init failed, fallback to silent mode: {e}")
        return False
