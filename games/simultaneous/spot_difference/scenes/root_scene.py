import time
from datetime import datetime

import pygame

from core.asset_loader import load_image_if_exists, project_path
from core.base_scene import BaseScene
from games.common.anaglyph import FILTER_LR, FILTER_RL, GLASSES_BACKGROUND, MODE_GLASSES, apply_filter
from ..services import SpotDifferenceBoardService, SpotDifferenceScoringService, SpotDifferenceSessionService


class SpotDifferenceScene(BaseScene):
    STATE_HOME = "home"
    STATE_HELP = "help"
    STATE_PLAY = "play"
    STATE_RESULT = "result"
    MODE_NAKED = "naked"
    MODE_GLASSES = MODE_GLASSES
    FILTER_LR = FILTER_LR
    FILTER_RL = FILTER_RL

    def __init__(self, manager):
        super().__init__(manager)
        self.width = 900
        self.height = 700
        self.state = self.STATE_HOME
        self.mode = self.MODE_NAKED
        self.filter_direction = self.FILTER_LR
        self.show_filter_picker = False
        self.home_focus = 0
        self.result_focus = 0
        self.selected_index = 0
        self.found_indices = set()
        self.pending_indices = set()
        self.round_flash_until = 0.0
        self.feedback_text = ""
        self.feedback_color = (255, 255, 255)
        self.feedback_until = 0.0
        self.final_stats = {}
        self.failure_count = 0
        self.board_service = SpotDifferenceBoardService()
        self.scoring = SpotDifferenceScoringService()
        self.session = SpotDifferenceSessionService(self._session_seconds())
        self.round_data = {"left": [], "right": [], "diff_index": 0}
        self._refresh_fonts()
        self._build_ui()
        self._new_round()

    def _refresh_fonts(self):
        self.title_font = self.create_font(54)
        self.sub_font = self.create_font(26)
        self.option_font = self.create_font(28)
        self.body_font = self.create_font(22)
        self.small_font = self.create_font(18)

    def _build_ui(self):
        card_w = min(560, self.width - 120)
        start_x = self.width // 2 - card_w // 2
        self.btn_naked = pygame.Rect(start_x, 208, card_w, 58)
        self.btn_glasses = pygame.Rect(start_x, 282, card_w, 58)
        self.btn_help = pygame.Rect(start_x, 356, card_w, 58)
        self.btn_back = pygame.Rect(self.width - 110, 18, 88, 36)
        self.btn_home = pygame.Rect(self.width - 110, 18, 88, 36)
        self.btn_confirm = pygame.Rect(self.width // 2 - 94, self.height - 58, 188, 44)
        self.btn_continue = pygame.Rect(self.width // 2 - 210, self.height - 100, 180, 48)
        self.btn_exit = pygame.Rect(self.width // 2 + 30, self.height - 100, 180, 48)
        self.help_ok = pygame.Rect(self.width // 2 - 90, self.height - 90, 180, 54)
        self.filter_modal = pygame.Rect(self.width // 2 - 250, self.height // 2 - 128, 500, 220)
        self.filter_lr = pygame.Rect(self.filter_modal.x + 24, self.filter_modal.y + 68, 210, 46)
        self.filter_rl = pygame.Rect(self.filter_modal.x + 266, self.filter_modal.y + 68, 210, 46)
        self.filter_start = pygame.Rect(self.filter_modal.centerx - 90, self.filter_modal.y + 150, 180, 44)
        gap = 52
        top = 148
        height = self.height - 296
        panel_width = (self.width - 168 - gap) // 2
        self.left_panel = pygame.Rect(84, top, panel_width, height)
        self.right_panel = pygame.Rect(self.left_panel.right + gap, top, panel_width, height)
        self.center_divider_x = self.width // 2

    def on_resize(self, width, height):
        self.width = width
        self.height = height
        self._build_ui()
        self._new_round()

    def reset(self):
        self.state = self.STATE_HOME
        self.mode = self.MODE_NAKED
        self.filter_direction = self.FILTER_LR
        self.show_filter_picker = False
        self.home_focus = 0
        self.result_focus = 0
        self.selected_index = 0
        self.found_indices = set()
        self.pending_indices = set()
        self.feedback_text = ""
        self.failure_count = 0
        self.scoring.reset()
        self.session.reset()
        self.final_stats = {}
        self._new_round()

    def _session_seconds(self):
        try:
            minutes = int(self.manager.settings.get("session_duration_minutes", 5))
        except (TypeError, ValueError):
            minutes = 5
        return max(60, minutes * 60)

    def _load_ui_icon(self, icon_name, light=False, size=(18, 18)):
        suffix = "light" if light else "dark"
        return load_image_if_exists(project_path("assets", "ui", f"{icon_name}_{suffix}.png"), size)

    def _draw_button(self, screen, rect, text, color, text_color=(255, 255, 255), icon_name=None, selected=False):
        hovered = rect.collidepoint(pygame.mouse.get_pos())
        fill = tuple(min(255, c + 18) for c in color) if hovered else color
        border = (255, 255, 255) if hovered else (202, 223, 246)
        if selected:
            glow_rect = rect.inflate(10, 10)
            pygame.draw.rect(screen, (255, 248, 196), glow_rect, border_radius=14)
            fill = tuple(min(255, c + 24) for c in color)
            border = (255, 244, 160)
        pygame.draw.rect(screen, fill, rect, border_radius=10)
        pygame.draw.rect(screen, border, rect, 3 if selected else 2, border_radius=10)
        label = self.option_font.render(text, True, text_color)
        icon = self._load_ui_icon(icon_name, light=sum(text_color) > 500) if icon_name else None
        gap = 8 if icon is not None else 0
        width = label.get_width() + (icon.get_width() + gap if icon is not None else 0)
        start_x = rect.centerx - width // 2
        if icon is not None:
            screen.blit(icon, (start_x, rect.centery - icon.get_height() // 2))
            start_x += icon.get_width() + gap
        screen.blit(label, (start_x, rect.centery - label.get_height() // 2))

    def _draw_filter_option(self, screen, rect, text, left_color, right_color, selected):
        self._draw_button(screen, rect, "", (244, 247, 255), text_color=(62, 72, 98), selected=selected)
        preview_rect = pygame.Rect(rect.x + 16, rect.y + 10, 56, rect.height - 20)
        left_rect = pygame.Rect(preview_rect.x, preview_rect.y, preview_rect.width // 2, preview_rect.height)
        right_rect = pygame.Rect(left_rect.right, preview_rect.y, preview_rect.width - left_rect.width, preview_rect.height)
        pygame.draw.rect(screen, left_color, left_rect, border_top_left_radius=8, border_bottom_left_radius=8)
        pygame.draw.rect(screen, right_color, right_rect, border_top_right_radius=8, border_bottom_right_radius=8)
        pygame.draw.rect(screen, (255, 255, 255), preview_rect, 2, border_radius=8)
        text_surface = self.small_font.render(text, True, (62, 72, 98))
        screen.blit(text_surface, (preview_rect.right + 16, rect.centery - text_surface.get_height() // 2))

    def _new_round(self):
        self.found_indices = set()
        self.pending_indices = set()
        self.round_data = self.board_service.create_round(self.left_panel, self._target_difference_count())
        self.selected_index = min(self.selected_index, len(self.round_data["right"]) - 1)

    def _target_difference_count(self):
        progress = 0.0
        if self.state == self.STATE_PLAY and self._session_seconds() > 0:
            progress = min(1.0, self.session.session_elapsed / max(1, self._session_seconds()))
        if progress < 0.25:
            return 2
        if progress < 0.5:
            return 3
        if progress < 0.75:
            return 4
        return 5

    def _start_game(self):
        self.state = self.STATE_PLAY
        self.scoring.reset()
        self.failure_count = 0
        self.session.session_seconds = self._session_seconds()
        self.session.start()
        self.feedback_text = ""
        self.selected_index = 0
        self._new_round()

    def _finish_game(self):
        self.state = self.STATE_RESULT
        duration = int(self.session.session_elapsed)
        total = self.scoring.success_count + self.failure_count
        accuracy = round((self.scoring.success_count / total) * 100, 1) if total else 0.0
        self.final_stats = {
            "duration": duration,
            "success": self.scoring.success_count,
            "score": self.scoring.score,
            "accuracy": accuracy,
            "best_combo": self.scoring.best_combo,
            "encouragement": self._result_encouragement(),
            "mode": self.mode,
            "filter_direction": self.filter_direction,
        }
        self._save_result()

    def _result_encouragement(self):
        if self.scoring.best_combo >= 5:
            return self.manager.t("spot_difference.result.encourage.combo")
        if self.scoring.success_count >= 8:
            return self.manager.t("spot_difference.result.encourage.clear")
        return self.manager.t("spot_difference.result.encourage.keep")

    def _save_result(self):
        data_manager = getattr(self.manager, "data_manager", None)
        if not data_manager:
            return
        total = self.scoring.success_count + self.failure_count
        payload = {
            "timestamp": datetime.now().isoformat(),
            "game_id": "simultaneous.spot_difference",
            "difficulty_level": 3,
            "total_questions": total,
            "correct_count": self.scoring.success_count,
            "wrong_count": self.failure_count,
            "duration_seconds": float(self.final_stats.get("duration", 0)),
            "accuracy_rate": self.final_stats.get("accuracy", 0.0),
            "training_metrics": {
                "binocular_merge_accuracy": self.final_stats.get("accuracy", 0.0),
                "best_combo": self.scoring.best_combo,
            },
        }
        data_manager.save_training_session(payload)

    def _set_feedback(self, key, color):
        self.feedback_text = self.manager.t(key)
        self.feedback_color = color
        self.feedback_until = time.time() + 1.1

    def _go_category(self):
        self.manager.set_scene("category")

    def _go_menu(self):
        self.manager.set_scene("menu")

    def _confirm_selection(self):
        pending = set(self.pending_indices)
        if not pending and self.selected_index not in self.found_indices:
            pending = {self.selected_index}
        if not pending:
            self._set_feedback("spot_difference.feedback.already", (120, 146, 190))
            return
        if pending.intersection(self.found_indices):
            self._set_feedback("spot_difference.feedback.already", (120, 146, 190))
            self.pending_indices.clear()
            return
        if pending.issubset(set(self.round_data["diff_indices"])):
            for _ in pending:
                self.scoring.on_success()
            self.found_indices.update(pending)
            self.pending_indices.clear()
            if len(self.found_indices) >= len(self.round_data["diff_indices"]):
                self.round_flash_until = time.time() + 0.55
                self._set_feedback("spot_difference.feedback.round_clear", (90, 226, 132))
            else:
                self._set_feedback("spot_difference.feedback.success", (90, 226, 132))
        else:
            self.scoring.on_failure()
            self.failure_count += 1
            self.pending_indices.clear()
            self._set_feedback("spot_difference.feedback.fail", (238, 118, 118))

    def _toggle_pending_selection(self, index):
        if index in self.found_indices:
            self._set_feedback("spot_difference.feedback.already", (120, 146, 190))
            return
        if index in self.pending_indices:
            self.pending_indices.remove(index)
            if self.selected_index == index:
                self.selected_index = -1
            self._set_feedback("spot_difference.feedback.unselect", (130, 146, 188))
        else:
            self.pending_indices.add(index)
            self.selected_index = index
            self._set_feedback("spot_difference.feedback.select", (96, 156, 214))

    def _draw_chip(self, screen, rect, text, bg_color, text_color=(255, 255, 255)):
        pygame.draw.rect(screen, bg_color, rect, border_radius=rect.height // 2)
        font = self.option_font
        label = font.render(text, True, text_color)
        if label.get_width() > rect.width - 24:
            font = self.body_font
            label = font.render(text, True, text_color)
        if label.get_width() > rect.width - 20:
            font = self.small_font
            label = font.render(text, True, text_color)
        screen.blit(label, (rect.centerx - label.get_width() // 2, rect.centery - label.get_height() // 2))

    def _draw_background(self, screen):
        top = (230, 243, 255)
        bottom = (215, 236, 252)
        for y in range(self.height):
            t = y / max(1, self.height - 1)
            color = (
                int(top[0] * (1 - t) + bottom[0] * t),
                int(top[1] * (1 - t) + bottom[1] * t),
                int(top[2] * (1 - t) + bottom[2] * t),
            )
            pygame.draw.line(screen, color, (0, y), (self.width, y))
        if self.state == self.STATE_PLAY and self.mode == self.MODE_GLASSES:
            overlay = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
            overlay.fill(GLASSES_BACKGROUND)
            screen.blit(overlay, (0, 0))

    def _draw_boards(self, screen):
        pygame.draw.line(
            screen,
            (164, 186, 216),
            (self.center_divider_x, self.left_panel.top + 16),
            (self.center_divider_x, self.left_panel.bottom - 16),
            3,
        )

        left_shapes = pygame.Surface((self.left_panel.width, self.left_panel.height), pygame.SRCALPHA)
        right_shapes = pygame.Surface((self.right_panel.width, self.right_panel.height), pygame.SRCALPHA)
        left_outline = pygame.Surface((self.left_panel.width, self.left_panel.height), pygame.SRCALPHA)
        right_outline = pygame.Surface((self.right_panel.width, self.right_panel.height), pygame.SRCALPHA)
        left_data = self.round_data["left"]
        right_data = self.round_data["right"]
        for item in left_data:
            self.board_service.draw_shape(left_outline, item["shape"], item["center"], item["size"], (42, 54, 76, 92), outline_width=2)
            self.board_service.draw_shape(left_shapes, item["shape"], item["center"], item["size"], item["color"])
        for index, item in enumerate(right_data):
            self.board_service.draw_shape(right_outline, item["shape"], item["center"], item["size"], (42, 54, 76, 92), outline_width=2)
            self.board_service.draw_shape(right_shapes, item["shape"], item["center"], item["size"], item["color"])
            if index in self.found_indices:
                found = pygame.Rect(0, 0, item["size"] + 26, item["size"] + 26)
                found.center = item["center"]
                pygame.draw.rect(right_shapes, (98, 180, 116, 220), found, 4, border_radius=12)
            elif index in self.pending_indices:
                marked = pygame.Rect(0, 0, item["size"] + 24, item["size"] + 24)
                marked.center = item["center"]
                pygame.draw.rect(right_shapes, (96, 156, 214, 220), marked, 4, border_radius=12)
            if index == self.selected_index:
                focus = pygame.Rect(0, 0, item["size"] + 22, item["size"] + 22)
                focus.center = item["center"]
                pygame.draw.rect(right_shapes, (255, 239, 152, 210), focus, 3, border_radius=10)
        if self.mode == self.MODE_GLASSES:
            left_shapes = apply_filter(left_shapes, self.mode, self.filter_direction, "left")
            right_shapes = apply_filter(right_shapes, self.mode, self.filter_direction, "right")
        screen.blit(left_outline, self.left_panel.topleft)
        screen.blit(right_outline, self.right_panel.topleft)
        screen.blit(left_shapes, self.left_panel.topleft)
        screen.blit(right_shapes, self.right_panel.topleft)

    def _draw_home(self, screen):
        title = self.title_font.render(self.manager.t("spot_difference.title"), True, (34, 60, 96))
        subtitle = self.sub_font.render(self.manager.t("spot_difference.subtitle"), True, (86, 104, 130))
        screen.blit(title, (self.width // 2 - title.get_width() // 2, 82))
        screen.blit(subtitle, (self.width // 2 - subtitle.get_width() // 2, 138))
        self._draw_button(screen, self.btn_naked, self.manager.t("spot_difference.home.naked"), (96, 140, 214), selected=self.home_focus == 0)
        self._draw_button(screen, self.btn_glasses, self.manager.t("spot_difference.home.glasses"), (110, 128, 172), selected=self.home_focus == 1)
        self._draw_button(screen, self.btn_help, self.manager.t("spot_difference.home.help"), (124, 140, 168), icon_name="question", selected=self.home_focus == 2)
        self._draw_button(screen, self.btn_back, self.manager.t("common.back"), (86, 116, 170), icon_name="back_arrow", selected=self.home_focus == 3)

    def _draw_help(self, screen):
        title = self.title_font.render(self.manager.t("spot_difference.help.title"), True, (34, 60, 96))
        screen.blit(title, (self.width // 2 - title.get_width() // 2, 68))
        steps = [
            self.manager.t("spot_difference.help.step1"),
            self.manager.t("spot_difference.help.step2"),
            self.manager.t("spot_difference.help.step3"),
        ]
        card_w = self.width - 180
        card_h = 94
        for idx, text in enumerate(steps):
            card = pygame.Rect(90, 156 + idx * 106, card_w, card_h)
            pygame.draw.rect(screen, (246, 250, 255), card, border_radius=18)
            pygame.draw.rect(screen, (196, 212, 234), card, 2, border_radius=18)
            badge = pygame.Rect(card.x + 14, card.y + 18, 38, 38)
            pygame.draw.ellipse(screen, (244, 210, 126), badge)
            num = self.body_font.render(str(idx + 1), True, (92, 76, 34))
            screen.blit(num, (badge.centerx - num.get_width() // 2, badge.centery - num.get_height() // 2))
            self._draw_help_illustration(screen, idx, card)
            line = self.body_font.render(text, True, (72, 90, 116))
            screen.blit(line, (card.x + 162, card.y + 22))
        self._draw_button(screen, self.help_ok, self.manager.t("spot_difference.help.ok"), (244, 208, 120), text_color=(92, 76, 34), icon_name="check")

    def _draw_help_illustration(self, screen, idx, card):
        area = pygame.Rect(card.x + 64, card.y + 16, 78, card.height - 32)
        pygame.draw.rect(screen, (232, 241, 252), area, border_radius=14)
        if idx == 0:
            left_dot = (area.centerx - 16, area.centery)
            right_dot = (area.centerx + 16, area.centery)
            pygame.draw.circle(screen, (255, 172, 92), left_dot, 10)
            pygame.draw.circle(screen, (255, 172, 92), right_dot, 10)
            pygame.draw.line(screen, (170, 184, 206), (area.centerx, area.y + 10), (area.centerx, area.bottom - 10), 2)
        elif idx == 1:
            pygame.draw.line(screen, (170, 184, 206), (area.centerx, area.y + 8), (area.centerx, area.bottom - 8), 2)
            focus = pygame.Rect(area.centerx + 6, area.centery - 16, 24, 24)
            pygame.draw.rect(screen, (255, 239, 152), focus, 3, border_radius=8)
            pygame.draw.polygon(screen, (96, 116, 156), [(area.x + 10, area.centery), (area.x + 24, area.centery - 10), (area.x + 24, area.centery + 10)])
        else:
            pygame.draw.line(screen, (170, 184, 206), (area.centerx, area.y + 8), (area.centerx, area.bottom - 8), 2)
            left_shape = [(area.centerx - 24, area.centery - 12), (area.centerx - 34, area.centery + 10), (area.centerx - 14, area.centery + 10)]
            right_shape = pygame.Rect(area.centerx + 10, area.centery - 12, 22, 22)
            pygame.draw.polygon(screen, (162, 228, 168), left_shape)
            pygame.draw.rect(screen, (122, 190, 255), right_shape, border_radius=6)
            pygame.draw.circle(screen, (92, 154, 106), (area.centerx + 26, area.centery + 20), 6)

    def _draw_filter_picker(self, screen):
        overlay = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        overlay.fill((24, 32, 46, 136))
        screen.blit(overlay, (0, 0))
        pygame.draw.rect(screen, (249, 251, 255), self.filter_modal, border_radius=18)
        pygame.draw.rect(screen, (190, 206, 228), self.filter_modal, 2, border_radius=18)
        title = self.sub_font.render(self.manager.t("spot_difference.filter.pick"), True, (52, 70, 100))
        screen.blit(title, (self.filter_modal.centerx - title.get_width() // 2, self.filter_modal.y + 20))
        self._draw_filter_option(screen, self.filter_lr, self.manager.t("spot_difference.filter.lr"), (255, 0, 0), (0, 0, 255), self.filter_direction == self.FILTER_LR)
        self._draw_filter_option(screen, self.filter_rl, self.manager.t("spot_difference.filter.rl"), (0, 0, 255), (255, 0, 0), self.filter_direction == self.FILTER_RL)
        self._draw_button(screen, self.filter_start, self.manager.t("spot_difference.filter.start"), (92, 152, 114), icon_name="check")

    def _draw_play(self, screen):
        chip = pygame.Rect(self.width // 2 - 106, 18, 212, 38)
        time_left = max(0, int(self._session_seconds() - self.session.session_elapsed))
        self._draw_chip(screen, chip, self.manager.t("spot_difference.time", sec=f"{time_left // 60:02d}:{time_left % 60:02d}"), (86, 116, 170))
        score_text = self.body_font.render(self.manager.t("spot_difference.score", score=self.scoring.score), True, (44, 60, 88))
        screen.blit(score_text, (84, 22))
        target_chip = pygame.Rect(84, 56, 196, 34)
        remaining = len(self.round_data["diff_indices"]) - len(self.found_indices)
        self._draw_chip(
            screen,
            target_chip,
            self.manager.t("spot_difference.target", remaining=remaining),
            (244, 210, 126),
            text_color=(88, 72, 32),
        )
        tip = self.small_font.render(self.manager.t("spot_difference.play.guide"), True, (54, 70, 96))
        screen.blit(tip, (self.width // 2 - tip.get_width() // 2, 68))
        self._draw_button(screen, self.btn_home, self.manager.t("common.back"), (86, 116, 170), icon_name="back_arrow")
        if self.round_flash_until > time.time():
            flash = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
            flash.fill((140, 218, 150, 18))
            screen.blit(flash, (0, 0))
        self._draw_boards(screen)
        if self.feedback_text:
            feedback = self.option_font.render(self.feedback_text, True, self.feedback_color)
            screen.blit(feedback, (self.width // 2 - feedback.get_width() // 2, self.height - 122))
        self._draw_button(screen, self.btn_confirm, self.manager.t("spot_difference.confirm"), (84, 148, 108), icon_name="check")

    def _draw_result(self, screen):
        title = self.title_font.render(self.manager.t("spot_difference.result.title"), True, (34, 60, 96))
        screen.blit(title, (self.width // 2 - title.get_width() // 2, 74))
        mode_text = self.manager.t("spot_difference.mode.naked") if self.final_stats.get("mode") == self.MODE_NAKED else self.manager.t("spot_difference.mode.glasses")
        filter_text = "-"
        if self.final_stats.get("mode") == self.MODE_GLASSES:
            filter_text = self.manager.t("spot_difference.filter.lr") if self.final_stats.get("filter_direction") == self.FILTER_LR else self.manager.t("spot_difference.filter.rl")
        lines = [
            self.manager.t("spot_difference.result.duration", sec=self.final_stats.get("duration", 0)),
            self.manager.t("spot_difference.result.success", n=self.final_stats.get("success", 0)),
            self.manager.t("spot_difference.result.score", n=self.final_stats.get("score", 0)),
            self.manager.t("spot_difference.result.mode", mode=mode_text),
            self.manager.t("spot_difference.result.filter", direction=filter_text),
        ]
        for idx, text in enumerate(lines):
            line = self.body_font.render(text, True, (66, 84, 114))
            screen.blit(line, (self.width // 2 - line.get_width() // 2, 176 + idx * 38))
        encouragement = self.body_font.render(self.final_stats.get("encouragement", ""), True, (88, 118, 82))
        screen.blit(encouragement, (self.width // 2 - encouragement.get_width() // 2, 372))
        self._draw_button(screen, self.btn_continue, self.manager.t("spot_difference.result.continue"), (84, 148, 108), icon_name="check", selected=self.result_focus == 0)
        self._draw_button(screen, self.btn_exit, self.manager.t("spot_difference.result.exit"), (120, 134, 168), icon_name="cross", selected=self.result_focus == 1)

    def handle_events(self, events):
        for event in events:
            if self.show_filter_picker:
                if event.type == pygame.KEYDOWN:
                    if event.key in (pygame.K_LEFT, pygame.K_RIGHT):
                        self.filter_direction = self.FILTER_RL if self.filter_direction == self.FILTER_LR else self.FILTER_LR
                    elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
                        self.show_filter_picker = False
                        self._start_game()
                    elif event.key == pygame.K_ESCAPE:
                        self.show_filter_picker = False
                elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    pos = getattr(event, "pos", pygame.mouse.get_pos())
                    if self.filter_lr.collidepoint(pos):
                        self.filter_direction = self.FILTER_LR
                    elif self.filter_rl.collidepoint(pos):
                        self.filter_direction = self.FILTER_RL
                    elif self.filter_start.collidepoint(pos):
                        self.show_filter_picker = False
                        self._start_game()
            elif self.state == self.STATE_HOME:
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        self._go_category()
                    elif event.key in (pygame.K_UP, pygame.K_LEFT):
                        self.home_focus = (self.home_focus - 1) % 4
                    elif event.key in (pygame.K_DOWN, pygame.K_RIGHT):
                        self.home_focus = (self.home_focus + 1) % 4
                    elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
                        if self.home_focus == 0:
                            self.mode = self.MODE_NAKED
                            self._start_game()
                        elif self.home_focus == 1:
                            self.mode = self.MODE_GLASSES
                            self.show_filter_picker = True
                        elif self.home_focus == 2:
                            self.state = self.STATE_HELP
                        else:
                            self._go_category()
                elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    pos = getattr(event, "pos", pygame.mouse.get_pos())
                    if self.btn_naked.collidepoint(pos):
                        self.mode = self.MODE_NAKED
                        self._start_game()
                    elif self.btn_glasses.collidepoint(pos):
                        self.mode = self.MODE_GLASSES
                        self.show_filter_picker = True
                    elif self.btn_help.collidepoint(pos):
                        self.state = self.STATE_HELP
                    elif self.btn_back.collidepoint(pos):
                        self._go_category()
            elif self.state == self.STATE_HELP:
                if event.type == pygame.KEYDOWN and event.key in (pygame.K_ESCAPE, pygame.K_RETURN, pygame.K_SPACE):
                    self.state = self.STATE_HOME
                elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1 and self.help_ok.collidepoint(getattr(event, "pos", pygame.mouse.get_pos())):
                    self.state = self.STATE_HOME
            elif self.state == self.STATE_PLAY:
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        self._go_category()
                    elif event.key == pygame.K_LEFT:
                        self.selected_index = max(0, self.selected_index - 1)
                    elif event.key == pygame.K_RIGHT:
                        self.selected_index = min(len(self.round_data["right"]) - 1, self.selected_index + 1)
                    elif event.key == pygame.K_UP:
                        self.selected_index = max(0, self.selected_index - 3)
                    elif event.key == pygame.K_DOWN:
                        self.selected_index = min(len(self.round_data["right"]) - 1, self.selected_index + 3)
                    elif event.key == pygame.K_SPACE:
                        self._toggle_pending_selection(self.selected_index)
                    elif event.key == pygame.K_RETURN:
                        self._confirm_selection()
                elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    pos = getattr(event, "pos", pygame.mouse.get_pos())
                    if self.btn_home.collidepoint(pos):
                        self._go_category()
                    elif self.btn_confirm.collidepoint(pos):
                        self._confirm_selection()
                    else:
                        for idx, item in enumerate(self.round_data["right"]):
                            rect = pygame.Rect(0, 0, item["size"] + 20, item["size"] + 20)
                            rect.center = (self.right_panel.x + item["center"][0], self.right_panel.y + item["center"][1])
                            if rect.collidepoint(pos):
                                self.selected_index = idx
                                self._toggle_pending_selection(idx)
                                break
            else:
                if event.type == pygame.KEYDOWN:
                    if event.key in (pygame.K_LEFT, pygame.K_UP):
                        self.result_focus = (self.result_focus - 1) % 2
                    elif event.key in (pygame.K_RIGHT, pygame.K_DOWN):
                        self.result_focus = (self.result_focus + 1) % 2
                    elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
                        if self.result_focus == 0:
                            self.state = self.STATE_HOME
                        else:
                            self._go_menu()
                    elif event.key == pygame.K_ESCAPE:
                        self._go_menu()
                elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    pos = getattr(event, "pos", pygame.mouse.get_pos())
                    if self.btn_continue.collidepoint(pos):
                        self.state = self.STATE_HOME
                    elif self.btn_exit.collidepoint(pos):
                        self._go_menu()

    def update(self):
        now = time.time()
        if self.state == self.STATE_PLAY:
            self.session.tick(now)
            if self.round_flash_until and now > self.round_flash_until:
                self.round_flash_until = 0.0
                self._new_round()
            if self.session.is_complete():
                self._finish_game()
        if self.feedback_text and now > self.feedback_until:
            self.feedback_text = ""

    def draw(self, screen):
        self.refresh_fonts_if_needed()
        self._draw_background(screen)
        if self.state == self.STATE_HOME:
            self._draw_home(screen)
        elif self.state == self.STATE_HELP:
            self._draw_help(screen)
        elif self.state == self.STATE_PLAY:
            self._draw_play(screen)
        else:
            self._draw_result(screen)
        if self.show_filter_picker:
            self._draw_filter_picker(screen)
