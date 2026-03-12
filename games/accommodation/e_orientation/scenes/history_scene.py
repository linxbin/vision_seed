import pygame
from datetime import datetime, timedelta
from core.base_scene import BaseScene
from core.ui_theme import PlatformTheme, draw_card, draw_chip, draw_platform_background
from ..services import ETrainingRecordsService
from config import SCREEN_WIDTH, E_SIZE_LEVELS


class HistoryScene(BaseScene):
    """历史记录场景 - 支持筛选、排序与分页查看。"""
    E_TRAINING_GAME_ID = "accommodation.e_orientation"

    def __init__(self, manager):
        super().__init__(manager)
        self._refresh_fonts()

        self.width = SCREEN_WIDTH
        self.height = 700
        self.layout_offset_x = 0

        self.back_button_rect = pygame.Rect(self.width - 80, 20, 60, 30)
        self.records_per_page = 8
        self.current_page = 0
        self.total_pages = 1

        self.raw_records = []
        self.filtered_records = []

        self.date_filter = "all"  # all / 7d / 30d
        self.level_filter = 0     # 0 means all
        self.sort_mode = "time"   # time / accuracy

        self.records_service = ETrainingRecordsService(self.manager.data_manager)
        self._reflow_layout()

    def _refresh_fonts(self):
        self.title_font = self.create_font(48)
        self.header_font = self.create_font(28)
        self.record_font = self.create_font(22)
        self.small_font = self.create_font(20)

    def _create_filter_controls(self):
        offset_x = self.layout_offset_x
        y = 118
        self.date_all_rect = pygame.Rect(offset_x + 120, y, 60, 32)
        self.date_7d_rect = pygame.Rect(offset_x + 186, y, 60, 32)
        self.date_30d_rect = pygame.Rect(offset_x + 252, y, 60, 32)
        self.level_dec_rect = pygame.Rect(offset_x + 408, y, 32, 32)
        self.level_value_rect = pygame.Rect(offset_x + 444, y, 74, 32)
        self.level_inc_rect = pygame.Rect(offset_x + 522, y, 32, 32)
        self.sort_time_rect = pygame.Rect(offset_x + 640, y, 78, 32)
        self.sort_acc_rect = pygame.Rect(offset_x + 724, y, 116, 32)

    def _reflow_layout(self):
        base_width = SCREEN_WIDTH
        self.layout_offset_x = max(0, (self.width - base_width) // 2)
        self.back_button_rect = pygame.Rect(self.width - 80, 20, 60, 30)
        self._create_filter_controls()

    def on_resize(self, width, height):
        self.width = width
        self.height = height
        self._reflow_layout()

    def on_enter(self):
        if not self._ensure_scope():
            return
        self._load_records()

    def _ensure_scope(self):
        game_id = getattr(self.manager, "active_game_id", None)
        if isinstance(game_id, str) and game_id and game_id != self.E_TRAINING_GAME_ID:
            self.manager.set_scene("menu")
            return False
        return True

    def _return_scene_name(self):
        if getattr(self.manager, "active_game_id", None) == self.E_TRAINING_GAME_ID:
            return "game_host"
        return "menu"

    def _load_records(self):
        try:
            self.raw_records = self.records_service.get_sessions()
        except Exception as e:
            print(f"Error loading records: {e}")
            self.raw_records = []
        self._apply_filters()

    def _parse_timestamp(self, value):
        try:
            dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
            if dt.tzinfo is not None:
                dt = dt.astimezone().replace(tzinfo=None)
            return dt
        except Exception:
            return None

    def _apply_filters(self):
        records = list(self.raw_records)

        if self.date_filter != "all":
            now = datetime.now()
            days = 7 if self.date_filter == "7d" else 30
            threshold = now - timedelta(days=days)
            kept = []
            for r in records:
                dt = self._parse_timestamp(r.get("timestamp", ""))
                if dt and dt >= threshold:
                    kept.append(r)
            records = kept

        if self.level_filter > 0:
            records = [r for r in records if int(r.get("difficulty_level", 0)) == self.level_filter]

        if self.sort_mode == "accuracy":
            records.sort(key=lambda r: float(r.get("accuracy_rate", 0.0)), reverse=True)
        else:
            records.sort(key=lambda r: r.get("timestamp", ""), reverse=True)

        self.filtered_records = records
        self.total_pages = max(1, (len(self.filtered_records) + self.records_per_page - 1) // self.records_per_page)
        self.current_page = min(self.current_page, self.total_pages - 1)

    def _format_timestamp(self, timestamp_str):
        dt = self._parse_timestamp(timestamp_str)
        if dt:
            return dt.strftime("%Y-%m-%d %H:%M")
        return self.manager.t("history.invalid_date")

    def _fit_text(self, text, font, max_width):
        if font.size(text)[0] <= max_width:
            return text
        ellipsis = "..."
        trimmed = text
        while trimmed and font.size(trimmed + ellipsis)[0] > max_width:
            trimmed = trimmed[:-1]
        return (trimmed + ellipsis) if trimmed else ellipsis

    def _get_current_page_records(self):
        start_idx = self.current_page * self.records_per_page
        end_idx = start_idx + self.records_per_page
        return self.filtered_records[start_idx:end_idx]

    def _draw_back_button(self, screen, mouse_pos):
        is_hovered = self.back_button_rect.collidepoint(mouse_pos)
        draw_chip(screen, self.back_button_rect, hovered=is_hovered, radius=10)
        back_text = self.small_font.render(
            self.manager.t("history.back"),
            True,
            PlatformTheme.ACCENT_DARK if not is_hovered else (255, 250, 244),
        )
        screen.blit(
            back_text,
            (
                self.back_button_rect.centerx - back_text.get_width() // 2,
                self.back_button_rect.centery - back_text.get_height() // 2,
            ),
        )

    def _draw_chip(self, screen, rect, text, active, mouse_pos):
        hovered = rect.collidepoint(mouse_pos)
        if active:
            fill = PlatformTheme.ACCENT
            border = (255, 224, 177)
            color = (255, 255, 255)
        else:
            fill = PlatformTheme.CARD_HOVER if hovered else PlatformTheme.CARD_ALT
            border = PlatformTheme.BORDER_HOVER if hovered else PlatformTheme.BORDER
            color = PlatformTheme.TEXT_PRIMARY
        pygame.draw.rect(screen, fill, rect, border_radius=8)
        pygame.draw.rect(screen, border, rect, 2, border_radius=8)
        txt = self.small_font.render(text, True, color)
        screen.blit(txt, (rect.centerx - txt.get_width() // 2, rect.centery - txt.get_height() // 2))

    def _draw_filters(self, screen, mouse_pos):
        label_color = PlatformTheme.TEXT_MUTED
        offset_x = self.layout_offset_x
        date_label = self.small_font.render(self.manager.t("history.filter.date"), True, label_color)
        level_label = self.small_font.render(self.manager.t("history.filter.level"), True, label_color)
        sort_label = self.small_font.render(self.manager.t("history.filter.sort"), True, label_color)
        screen.blit(date_label, (offset_x + 60, 124))
        screen.blit(level_label, (offset_x + 346, 124))
        screen.blit(sort_label, (offset_x + 586, 124))

        self._draw_chip(
            screen, self.date_all_rect, self.manager.t("history.filter.all"), self.date_filter == "all", mouse_pos
        )
        self._draw_chip(
            screen, self.date_7d_rect, self.manager.t("history.filter.7d"), self.date_filter == "7d", mouse_pos
        )
        self._draw_chip(
            screen, self.date_30d_rect, self.manager.t("history.filter.30d"), self.date_filter == "30d", mouse_pos
        )

        self._draw_chip(screen, self.level_dec_rect, "-", False, mouse_pos)
        level_text = self.manager.t("history.filter.all") if self.level_filter == 0 else f"L{self.level_filter}"
        self._draw_chip(screen, self.level_value_rect, level_text, True, mouse_pos)
        self._draw_chip(screen, self.level_inc_rect, "+", False, mouse_pos)

        self._draw_chip(
            screen, self.sort_time_rect, self.manager.t("history.sort.time"), self.sort_mode == "time", mouse_pos
        )
        self._draw_chip(
            screen, self.sort_acc_rect, self.manager.t("history.sort.accuracy"), self.sort_mode == "accuracy", mouse_pos
        )

    def handle_events(self, events):
        mouse_pos = pygame.mouse.get_pos()
        for event in events:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.manager.set_scene(self._return_scene_name())
                elif event.key == pygame.K_LEFT:
                    self.current_page = max(0, self.current_page - 1)
                elif event.key == pygame.K_RIGHT:
                    self.current_page = min(self.total_pages - 1, self.current_page + 1)
                elif event.key == pygame.K_r:
                    self._load_records()
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if self.back_button_rect.collidepoint(mouse_pos):
                    self.manager.set_scene(self._return_scene_name())
                    return

                if self.date_all_rect.collidepoint(mouse_pos):
                    self.date_filter = "all"
                    self.current_page = 0
                    self._apply_filters()
                elif self.date_7d_rect.collidepoint(mouse_pos):
                    self.date_filter = "7d"
                    self.current_page = 0
                    self._apply_filters()
                elif self.date_30d_rect.collidepoint(mouse_pos):
                    self.date_filter = "30d"
                    self.current_page = 0
                    self._apply_filters()
                elif self.level_dec_rect.collidepoint(mouse_pos):
                    self.level_filter = max(0, self.level_filter - 1)
                    self.current_page = 0
                    self._apply_filters()
                elif self.level_inc_rect.collidepoint(mouse_pos):
                    self.level_filter = min(len(E_SIZE_LEVELS), self.level_filter + 1)
                    self.current_page = 0
                    self._apply_filters()
                elif self.sort_time_rect.collidepoint(mouse_pos):
                    self.sort_mode = "time"
                    self.current_page = 0
                    self._apply_filters()
                elif self.sort_acc_rect.collidepoint(mouse_pos):
                    self.sort_mode = "accuracy"
                    self.current_page = 0
                    self._apply_filters()

    def update(self):
        pass

    def draw(self, screen):
        self.refresh_fonts_if_needed()
        draw_platform_background(screen, self.width, self.height)
        mouse_pos = pygame.mouse.get_pos()

        title = self.title_font.render(self.manager.t("history.title"), True, PlatformTheme.TEXT_PRIMARY)
        screen.blit(title, (self.width // 2 - title.get_width() // 2, 34))

        info = self.manager.t("history.info_with_records") if self.filtered_records else self.manager.t("history.info_empty")
        info_surface = self.small_font.render(
            info,
            True,
            PlatformTheme.TEXT_MUTED if self.filtered_records else (170, 106, 106),
        )
        screen.blit(info_surface, (self.width // 2 - info_surface.get_width() // 2, 82))

        self._draw_filters(screen, mouse_pos)

        if not self.filtered_records:
            self._draw_back_button(screen, mouse_pos)
            return

        # 自适应列宽（时间列更宽）
        margin = self.layout_offset_x + 60
        table_left = margin
        table_right = self.width - margin
        table_width = table_right - table_left
        weights = [0.31, 0.10, 0.13, 0.13, 0.14, 0.19]
        col_widths = [int(table_width * w) for w in weights]
        col_widths[-1] += table_width - sum(col_widths)
        col_centers = []
        cursor = table_left
        for w in col_widths:
            col_centers.append(cursor + w // 2)
            cursor += w

        header_y = 164
        headers = [
            self.manager.t("history.header.datetime"),
            self.manager.t("history.header.level"),
            self.manager.t("history.header.questions"),
            self.manager.t("history.header.correct"),
            self.manager.t("history.header.accuracy"),
            self.manager.t("history.header.duration"),
        ]
        for i, header in enumerate(headers):
            text = self._fit_text(header, self.header_font, col_widths[i] - 10)
            surf = self.header_font.render(text, True, PlatformTheme.TEXT_PRIMARY)
            screen.blit(surf, (col_centers[i] - surf.get_width() // 2, header_y))

        pygame.draw.line(screen, PlatformTheme.BORDER, (table_left, header_y + 34), (table_right, header_y + 34), 2)

        current_records = self._get_current_page_records()
        row_start = header_y + 48
        row_height = 42
        for i, record in enumerate(current_records):
            y = row_start + i * row_height
            row_rect = pygame.Rect(table_left, y, table_width, row_height - 4)
            draw_card(screen, row_rect, alt=i % 2 == 1, radius=10)
            fg = PlatformTheme.TEXT_PRIMARY if i % 2 == 0 else PlatformTheme.TEXT_MUTED

            row = [
                self._format_timestamp(record.get("timestamp", "")),
                str(record.get("difficulty_level", "-")),
                str(record.get("total_questions", "-")),
                str(record.get("correct_count", "-")),
                f"{float(record.get('accuracy_rate', 0.0)):.1f}%",
                f"{float(record.get('duration_seconds', 0.0)):.2f}s",
            ]
            for j, cell in enumerate(row):
                text = self._fit_text(cell, self.record_font, col_widths[j] - 10)
                surf = self.record_font.render(text, True, fg)
                screen.blit(surf, (col_centers[j] - surf.get_width() // 2, y + (row_height - 4 - surf.get_height()) // 2))

        if self.total_pages > 1:
            page_info = self.manager.t("history.page_info", current=self.current_page + 1, total=self.total_pages)
            page_surf = self.small_font.render(page_info, True, PlatformTheme.TEXT_MUTED)
            screen.blit(page_surf, (self.width // 2 - page_surf.get_width() // 2, row_start + len(current_records) * row_height + 16))

        self._draw_back_button(screen, mouse_pos)
