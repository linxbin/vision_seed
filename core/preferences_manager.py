import json
import os
import sys
from typing import Dict, Any

from config import (
    DEFAULT_TOTAL_QUESTIONS,
    DEFAULT_START_LEVEL,
    MIN_LEVEL,
    MAX_LEVEL,
    MIN_QUESTIONS,
    MAX_QUESTIONS,
)


class PreferencesManager:
    """用户偏好管理器 - 负责用户偏好的持久化和读取。"""
    SUPPORTED_LANGUAGES = {"en-US", "zh-CN"}

    def __init__(self):
        self.project_root = self._get_project_root()
        self.config_dir = os.path.join(self.project_root, "config")
        self.preferences_file = os.path.join(self.config_dir, "user_preferences.json")
        os.makedirs(self.config_dir, exist_ok=True)

        if not os.path.exists(self.preferences_file):
            self.save_preferences(self.default_preferences())

    def _get_project_root(self) -> str:
        if getattr(sys, "frozen", False):
            return os.path.dirname(sys.executable)
        return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    def default_preferences(self) -> Dict[str, Any]:
        return {
            "start_level": DEFAULT_START_LEVEL,
            "total_questions": DEFAULT_TOTAL_QUESTIONS,
            "sound_enabled": True,
            "language": "en-US",
        }

    def _sanitize(self, preferences: Dict[str, Any]) -> Dict[str, Any]:
        defaults = self.default_preferences()
        merged = {**defaults, **(preferences or {})}

        try:
            merged["start_level"] = int(merged["start_level"])
        except (TypeError, ValueError):
            merged["start_level"] = defaults["start_level"]
        merged["start_level"] = max(MIN_LEVEL, min(MAX_LEVEL, merged["start_level"]))

        try:
            merged["total_questions"] = int(merged["total_questions"])
        except (TypeError, ValueError):
            merged["total_questions"] = defaults["total_questions"]
        merged["total_questions"] = max(MIN_QUESTIONS, min(MAX_QUESTIONS, merged["total_questions"]))

        merged["sound_enabled"] = bool(merged["sound_enabled"])

        language = merged.get("language", defaults["language"])
        if language not in self.SUPPORTED_LANGUAGES:
            language = defaults["language"]
        merged["language"] = language
        return merged

    def load_preferences(self) -> Dict[str, Any]:
        try:
            with open(self.preferences_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            sanitized = self._sanitize(data)
            if sanitized != data:
                self.save_preferences(sanitized)
            return sanitized
        except (json.JSONDecodeError, OSError) as e:
            print(f"Error loading preferences: {e}")
            defaults = self.default_preferences()
            self.save_preferences(defaults)
            return defaults

    def save_preferences(self, preferences: Dict[str, Any]) -> bool:
        try:
            sanitized = self._sanitize(preferences)
            with open(self.preferences_file, "w", encoding="utf-8") as f:
                json.dump(sanitized, f, ensure_ascii=False, indent=2)
            return True
        except OSError as e:
            print(f"Error saving preferences: {e}")
            return False
