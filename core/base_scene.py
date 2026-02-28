import os
import pygame
from core.app_paths import get_resource_path


class BaseScene:
    CHINESE_FONT_SCALE = 0.88

    def __init__(self, manager):
        self.manager = manager
        self._font_cache = {}
        self._font_language_marker = self.manager.settings.get("language", "en-US")

    def _get_chinese_font_path(self):
        font_path = get_resource_path("assets", "SimHei.ttf")
        return font_path if os.path.exists(font_path) else None

    def create_font(self, size, bold=False, italic=False):
        """根据当前语言创建字体；中文优先使用项目内置 TTF。"""
        language = self.manager.settings.get("language", "en-US")
        adjusted_size = size
        if language == "zh-CN":
            adjusted_size = max(10, int(round(size * self.CHINESE_FONT_SCALE)))

        cache_key = (language, adjusted_size, bold, italic)
        if cache_key in self._font_cache:
            return self._font_cache[cache_key]

        font = None
        if language == "zh-CN":
            font_path = self._get_chinese_font_path()
            if font_path:
                font = pygame.font.Font(font_path, adjusted_size)
            else:
                font = pygame.font.SysFont("SimHei", adjusted_size)
        else:
            font = pygame.font.SysFont(None, adjusted_size)

        font.set_bold(bold)
        font.set_italic(italic)
        self._font_cache[cache_key] = font
        return font

    def refresh_fonts_if_needed(self):
        """仅在语言切换时刷新字体引用，避免每帧重复刷新。"""
        current_language = self.manager.settings.get("language", "en-US")
        if current_language == self._font_language_marker:
            return
        self._font_language_marker = current_language
        refresher = getattr(self, "_refresh_fonts", None)
        if callable(refresher):
            refresher()

    def handle_events(self, events):
        pass

    def update(self):
        pass

    def draw(self, screen):
        pass

    def on_resize(self, width, height):
        pass
