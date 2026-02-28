import pygame
from core.base_scene import BaseScene


class ReportScene(BaseScene):

    def __init__(self, manager):
        super().__init__(manager)
        self._refresh_fonts()
        self.width = 900
        self.height = 700
        self.layout_offset_x = 0
        self.layout_offset_y = 0
        self._reflow_layout()
        self.prev_session = None

    def _refresh_fonts(self):
        self.title_font = self.create_font(52)
        self.badge_font = self.create_font(30)
        self.label_font = self.create_font(24)
        self.value_font = self.create_font(36)
        self.hint_font = self.create_font(20)
        self.trend_font = self.create_font(20)
        self.suggestion_font = self.create_font(22)

    def _create_ui(self):
        offset_x = self.layout_offset_x
        offset_y = self.layout_offset_y
        card_w = 280
        card_h = 82
        left_x = offset_x + 130
        right_x = offset_x + 490
        self.cards = [
            {"label_key": "report.total_questions", "field": "total", "x": left_x, "y": offset_y + 228, "w": card_w, "h": card_h},
            {"label_key": "report.correct", "field": "correct", "x": right_x, "y": offset_y + 228, "w": card_w, "h": card_h},
            {"label_key": "report.wrong", "field": "wrong", "x": left_x, "y": offset_y + 332, "w": card_w, "h": card_h},
            {"label_key": "report.accuracy", "field": "accuracy", "x": right_x, "y": offset_y + 332, "w": card_w, "h": card_h},
            {"label_key": "report.time_used", "field": "duration", "x": left_x, "y": offset_y + 436, "w": card_w, "h": card_h},
            {"label_key": "report.max_combo", "field": "max_combo", "x": right_x, "y": offset_y + 436, "w": card_w, "h": card_h},
        ]
        self.retry_button_rect = pygame.Rect(offset_x + 250, offset_y + 610, 170, 44)
        self.menu_button_rect = pygame.Rect(offset_x + 480, offset_y + 610, 170, 44)

    def _reflow_layout(self):
        base_width = 900
        base_height = 700
        self.layout_offset_x = max(0, (self.width - base_width) // 2)
        self.layout_offset_y = max(0, (self.height - base_height) // 2)
        self._create_ui()

    def on_resize(self, width, height):
        self.width = width
        self.height = height
        self._reflow_layout()

    def on_enter(self):
        sessions = self.manager.data_manager.get_all_sessions()
        self.prev_session = sessions[1] if len(sessions) > 1 else None

    def _accuracy_color(self, accuracy):
        if accuracy >= 80:
            return (100, 220, 140)
        if accuracy >= 50:
            return (235, 205, 90)
        return (235, 110, 110)

    def _result_text(self, accuracy):
        if accuracy >= 80:
            return self.manager.t("report.result_excellent")
        if accuracy >= 50:
            return self.manager.t("report.result_good")
        return self.manager.t("report.result_keep_going")

    def _draw_button(self, screen, rect, text, mouse_pos, base_color):
        hovered = rect.collidepoint(mouse_pos)
        fill = tuple(min(c + 25, 255) for c in base_color) if hovered else base_color
        border = (200, 220, 255) if hovered else (140, 170, 220)

        pygame.draw.rect(screen, fill, rect, border_radius=8)
        pygame.draw.rect(screen, border, rect, 2, border_radius=8)

        text_surface = self.label_font.render(text, True, (255, 255, 255))
        text_x = rect.centerx - text_surface.get_width() // 2
        text_y = rect.centery - text_surface.get_height() // 2
        screen.blit(text_surface, (text_x, text_y))

    def _fit_text(self, text, font, max_width):
        if font.size(text)[0] <= max_width:
            return text
        ellipsis = "..."
        trimmed = text
        while trimmed and font.size(trimmed + ellipsis)[0] > max_width:
            trimmed = trimmed[:-1]
        return (trimmed + ellipsis) if trimmed else ellipsis

    def _get_suggestion(self, accuracy):
        level = self.manager.settings.get("start_level", 3)
        if accuracy >= 85:
            return self.manager.t("report.suggestion_raise", level=max(1, level - 1))
        if accuracy < 60:
            return self.manager.t("report.suggestion_lower", level=min(8, level + 1))
        return self.manager.t("report.suggestion_keep", level=level)

    def _get_next_plan(self, accuracy, duration, total):
        current_level = self.manager.settings.get("start_level", 3)
        current_questions = self.manager.settings.get("total_questions", 30)
        avg_sec = (duration / total) if total > 0 else 2.0

        if accuracy >= 88 and avg_sec <= 2.0:
            next_level = max(1, current_level - 1)
        elif accuracy < 65:
            next_level = min(8, current_level + 1)
        else:
            next_level = current_level

        if accuracy >= 85 and avg_sec <= 2.2:
            next_questions = min(1000, current_questions + 10)
        elif accuracy < 60:
            next_questions = max(10, current_questions - 10)
        else:
            next_questions = current_questions

        target_minutes = max(3, min(20, round((next_questions * 2.0) / 60)))
        return self.manager.t(
            "report.next_plan",
            level=next_level,
            questions=next_questions,
            minutes=target_minutes,
        )

    def handle_events(self, events):
        mouse_pos = pygame.mouse.get_pos()
        for event in events:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RETURN:
                    self.manager.set_scene("training")
                elif event.key == pygame.K_ESCAPE:
                    self.manager.set_scene("menu")
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if self.retry_button_rect.collidepoint(mouse_pos):
                    self.manager.set_scene("training")
                elif self.menu_button_rect.collidepoint(mouse_pos):
                    self.manager.set_scene("menu")

    def draw(self, screen):
        self._refresh_fonts()
        screen.fill((24, 32, 52))

        correct = self.manager.current_result.get("correct", 0)
        wrong = self.manager.current_result.get("wrong", 0)
        total = self.manager.current_result.get("total", 0)
        duration = self.manager.current_result.get("duration", 0.0)
        max_combo = self.manager.current_result.get("max_combo", 0)
        accuracy = round((correct / total) * 100, 1) if total > 0 else 0.0
        mouse_pos = pygame.mouse.get_pos()

        # 标题与结果等级
        title = self.title_font.render(self.manager.t("report.title"), True, (255, 255, 255))
        screen.blit(title, (self.width // 2 - title.get_width() // 2, self.layout_offset_y + 80))

        badge_text = self._result_text(accuracy)
        badge_color = self._accuracy_color(accuracy)
        badge = self.badge_font.render(badge_text, True, badge_color)
        screen.blit(badge, (self.width // 2 - badge.get_width() // 2, self.layout_offset_y + 145))

        # 建议区固定在卡片上方安全区，使用较小字号避免与卡片重叠
        suggestion_raw = self._get_suggestion(accuracy)
        next_plan_raw = self._get_next_plan(accuracy, duration, total)
        suggestion_text = self._fit_text(suggestion_raw, self.trend_font, 760)
        next_plan_text = self._fit_text(next_plan_raw, self.hint_font, 760)
        suggestion = self.trend_font.render(suggestion_text, True, (130, 220, 175))
        next_plan = self.hint_font.render(next_plan_text, True, (188, 218, 255))
        suggestion_y = self.layout_offset_y + 178
        next_plan_y = self.layout_offset_y + 202
        screen.blit(suggestion, (self.width // 2 - suggestion.get_width() // 2, suggestion_y))
        screen.blit(next_plan, (self.width // 2 - next_plan.get_width() // 2, next_plan_y))

        # 结果卡片
        for card in self.cards:
            rect = pygame.Rect(card["x"], card["y"], card["w"], card["h"])
            pygame.draw.rect(screen, (38, 50, 78), rect, border_radius=10)
            pygame.draw.rect(screen, (82, 110, 165), rect, 2, border_radius=10)

            field = card["field"]
            if field == "total":
                text = self.manager.t("report.total_questions", total=total)
                color = (235, 235, 240)
            elif field == "correct":
                text = self.manager.t("report.correct", correct=correct)
                color = (120, 230, 155)
            elif field == "wrong":
                text = self.manager.t("report.wrong", wrong=wrong)
                color = (235, 130, 130)
            elif field == "accuracy":
                text = self.manager.t("report.accuracy", accuracy=accuracy)
                color = self._accuracy_color(accuracy)
            elif field == "max_combo":
                text = self.manager.t("report.max_combo", combo=max_combo)
                color = (255, 196, 112)
            else:
                text = self.manager.t("report.time_used", duration=duration)
                color = (170, 200, 255)

            text_surface = self.value_font.render(text, True, color)
            text_x = rect.centerx - text_surface.get_width() // 2
            text_y = rect.centery - text_surface.get_height() // 2
            screen.blit(text_surface, (text_x, text_y))

        # 趋势与建议
        if self.prev_session:
            prev_accuracy = float(self.prev_session.get("accuracy_rate", 0.0))
            prev_duration = float(self.prev_session.get("duration_seconds", 0.0))
            acc_delta = round(accuracy - prev_accuracy, 1)
            dur_delta = round(duration - prev_duration, 2)

            acc_arrow = "↑" if acc_delta > 0 else ("↓" if acc_delta < 0 else "→")
            dur_arrow = "↑" if dur_delta > 0 else ("↓" if dur_delta < 0 else "→")

            acc_text = self.manager.t("report.trend_accuracy", delta=f"{acc_delta:+.1f}", arrow=acc_arrow)
            dur_text = self.manager.t("report.trend_duration", delta=f"{dur_delta:+.2f}", arrow=dur_arrow)
            acc_surface = self.trend_font.render(self._fit_text(acc_text, self.trend_font, 820), True, (190, 210, 245))
            dur_surface = self.trend_font.render(self._fit_text(dur_text, self.trend_font, 820), True, (190, 210, 245))
            screen.blit(acc_surface, (self.width // 2 - acc_surface.get_width() // 2, self.layout_offset_y + 560))
            screen.blit(dur_surface, (self.width // 2 - dur_surface.get_width() // 2, self.layout_offset_y + 582))
        else:
            no_hist = self.trend_font.render(self.manager.t("report.trend_no_history"), True, (180, 190, 210))
            screen.blit(no_hist, (self.width // 2 - no_hist.get_width() // 2, self.layout_offset_y + 570))

        # 操作按钮
        self._draw_button(
            screen,
            self.retry_button_rect,
            self.manager.t("report.retry"),
            mouse_pos,
            (60, 150, 92),
        )
        self._draw_button(
            screen,
            self.menu_button_rect,
            self.manager.t("report.back_menu"),
            mouse_pos,
            (78, 104, 155),
        )

        # 快捷键提示
        hint = self.hint_font.render(self.manager.t("report.return_hint"), True, (180, 190, 210))
        screen.blit(hint, (self.width // 2 - hint.get_width() // 2, self.layout_offset_y + 665))
