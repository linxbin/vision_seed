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

    def fit_text_to_width(self, font, text, max_width, ellipsis="..."):
        """将文本裁剪到指定宽度内，必要时追加省略号。"""
        if max_width <= 0:
            return ""
        if font.size(text)[0] <= max_width:
            return text

        ellipsis_width = font.size(ellipsis)[0]
        if ellipsis_width >= max_width:
            return ""

        fitted = []
        current_width = 0
        for char in text:
            char_width = font.size(char)[0]
            if current_width + char_width + ellipsis_width > max_width:
                break
            fitted.append(char)
            current_width += char_width
        return "".join(fitted).rstrip() + ellipsis

    def wrap_text(self, font, text, max_width, max_lines=None, ellipsis=False):
        """按字符宽度进行换行，兼容中英文混排。"""
        content = (text or "").replace("\r\n", "\n").replace("\r", "\n")
        paragraphs = content.split("\n")
        lines = []
        truncated = False

        for paragraph in paragraphs:
            if not paragraph:
                lines.append("")
                if max_lines is not None and len(lines) >= max_lines:
                    truncated = True
                    break
                continue

            current = ""
            for char in paragraph:
                candidate = current + char
                if current and font.size(candidate)[0] > max_width:
                    lines.append(current.rstrip())
                    current = char.lstrip() if char.isspace() else char
                    if max_lines is not None and len(lines) >= max_lines:
                        truncated = True
                        break
                else:
                    current = candidate
            if truncated:
                break
            if current:
                lines.append(current.rstrip())
                if max_lines is not None and len(lines) >= max_lines:
                    truncated = True
                    break

        if not lines:
            lines = [""]

        if max_lines is not None and len(lines) > max_lines:
            lines = lines[:max_lines]
            truncated = True

        if ellipsis and truncated and lines:
            lines[-1] = self.fit_text_to_width(font, lines[-1].rstrip(), max_width)
        return lines

    def draw_text_block(
        self,
        screen,
        font,
        text,
        color,
        topleft,
        max_width,
        line_gap=6,
        max_lines=None,
        ellipsis=False,
    ):
        lines = self.wrap_text(font, text, max_width, max_lines=max_lines, ellipsis=ellipsis)
        y = topleft[1]
        line_height = font.get_height()
        for line in lines:
            surface = font.render(line, True, color)
            screen.blit(surface, (topleft[0], y))
            y += line_height + line_gap
        if lines:
            y -= line_gap
        return lines, y - topleft[1]

    def draw_session_hud(
        self,
        screen,
        *,
        top_font,
        meta_font,
        left_title,
        timer_text,
        center_text=None,
        left_lines=(),
        right_lines=(),
        play_area=None,
        top_y=18,
        left_x=24,
        center_y=44,
        meta_start_y=50,
        meta_gap=24,
        timer_color=(55, 82, 122),
        center_color=(55, 82, 122),
        left_title_color=(55, 82, 122),
        meta_color=(86, 104, 130),
        right_align=None,
    ):
        left_surface = top_font.render(left_title, True, left_title_color)
        screen.blit(left_surface, (left_x, top_y))

        timer_surface = top_font.render(timer_text, True, timer_color)
        screen.blit(timer_surface, (screen.get_width() // 2 - timer_surface.get_width() // 2, top_y - 4))

        if center_text:
            center_surface = top_font.render(center_text, True, center_color)
            screen.blit(center_surface, (screen.get_width() // 2 - center_surface.get_width() // 2, center_y))

        y = meta_start_y
        for text in left_lines:
            surface = meta_font.render(text, True, meta_color)
            screen.blit(surface, (left_x, y))
            y += meta_gap

        if right_align is None and play_area is not None:
            right_align = play_area.right
        elif right_align is None:
            right_align = screen.get_width() - 24

        y = meta_start_y
        for text in right_lines:
            surface = meta_font.render(text, True, meta_color)
            screen.blit(surface, (right_align - surface.get_width(), y))
            y += meta_gap

    def draw_two_column_stats(
        self,
        screen,
        *,
        font,
        entries,
        top_y,
        left_x,
        right_x,
        column_width,
        rows_per_column,
        row_gap=38,
        default_color=(58, 84, 118),
    ):
        for idx, entry in enumerate(entries):
            if isinstance(entry, tuple):
                text, color = entry
            else:
                text, color = entry, default_color
            column_x = left_x if idx < rows_per_column else right_x
            row_y = top_y + (idx % rows_per_column) * row_gap
            fitted = self.fit_text_to_width(font, text, column_width)
            surface = font.render(fitted, True, color)
            screen.blit(surface, (column_x, row_y))

    def play_correct_sound(self):
        sound_manager = getattr(self.manager, "sound_manager", None)
        if sound_manager is not None:
            sound_manager.play_correct()

    def play_wrong_sound(self):
        sound_manager = getattr(self.manager, "sound_manager", None)
        if sound_manager is not None:
            sound_manager.play_wrong()

    def play_completed_sound(self):
        sound_manager = getattr(self.manager, "sound_manager", None)
        if sound_manager is not None:
            sound_manager.play_completed()

    def handle_events(self, events):
        pass

    def update(self):
        pass

    def draw(self, screen):
        pass

    def on_resize(self, width, height):
        pass
