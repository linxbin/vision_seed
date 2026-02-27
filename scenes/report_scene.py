import pygame
from core.base_scene import BaseScene


class ReportScene(BaseScene):

    def __init__(self, manager):
        super().__init__(manager)
        self._refresh_fonts()
        self._create_ui()
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
        self.cards = [
            {"label_key": "report.total_questions", "field": "total", "x": 120, "y": 220, "w": 300, "h": 90},
            {"label_key": "report.correct", "field": "correct", "x": 480, "y": 220, "w": 300, "h": 90},
            {"label_key": "report.wrong", "field": "wrong", "x": 120, "y": 330, "w": 300, "h": 90},
            {"label_key": "report.accuracy", "field": "accuracy", "x": 480, "y": 330, "w": 300, "h": 90},
            {"label_key": "report.time_used", "field": "duration", "x": 300, "y": 440, "w": 300, "h": 90},
        ]
        self.retry_button_rect = pygame.Rect(250, 610, 170, 44)
        self.menu_button_rect = pygame.Rect(480, 610, 170, 44)

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

    def _get_suggestion(self, accuracy):
        level = self.manager.settings.get("start_level", 3)
        if accuracy >= 85:
            return self.manager.t("report.suggestion_raise", level=max(1, level - 1))
        if accuracy < 60:
            return self.manager.t("report.suggestion_lower", level=min(8, level + 1))
        return self.manager.t("report.suggestion_keep", level=level)

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
        accuracy = round((correct / total) * 100, 1) if total > 0 else 0.0
        mouse_pos = pygame.mouse.get_pos()

        # 标题与结果等级
        title = self.title_font.render(self.manager.t("report.title"), True, (255, 255, 255))
        screen.blit(title, (450 - title.get_width() // 2, 80))

        badge_text = self._result_text(accuracy)
        badge_color = self._accuracy_color(accuracy)
        badge = self.badge_font.render(badge_text, True, badge_color)
        screen.blit(badge, (450 - badge.get_width() // 2, 145))

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
            acc_surface = self.trend_font.render(acc_text, True, (190, 210, 245))
            dur_surface = self.trend_font.render(dur_text, True, (190, 210, 245))
            screen.blit(acc_surface, (450 - acc_surface.get_width() // 2, 560))
            screen.blit(dur_surface, (450 - dur_surface.get_width() // 2, 582))
        else:
            no_hist = self.trend_font.render(self.manager.t("report.trend_no_history"), True, (180, 190, 210))
            screen.blit(no_hist, (450 - no_hist.get_width() // 2, 570))

        suggestion = self.suggestion_font.render(self._get_suggestion(accuracy), True, (130, 220, 175))
        screen.blit(suggestion, (450 - suggestion.get_width() // 2, 535))

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
        screen.blit(hint, (450 - hint.get_width() // 2, 665))
