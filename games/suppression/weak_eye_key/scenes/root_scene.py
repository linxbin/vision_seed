import time
from datetime import datetime

import pygame

from core.asset_loader import load_image_if_exists, project_path
from core.base_scene import BaseScene
from games.common.anaglyph import BLUE_FILTER, FILTER_LR, FILTER_RL, GLASSES_BACKGROUND, GLASSES_BUTTON_COLOR, MODE_GLASSES, RED_FILTER, apply_filter
from ..services import WeakEyeKeyBoardService, WeakEyeKeyScoringService, WeakEyeKeySessionService


class WeakEyeKeyScene(BaseScene):
    STATE_HOME = "home"
    STATE_HELP = "help"
    STATE_PLAY = "play"
    STATE_RESULT = "result"
    MODE_GLASSES = MODE_GLASSES
    FILTER_LR = FILTER_LR
    FILTER_RL = FILTER_RL

    def __init__(self, manager):
        super().__init__(manager)
        self.width = 900
        self.height = 700
        self.state = self.STATE_HOME
        self.mode = self.MODE_GLASSES
        self.filter_direction = self.FILTER_LR
        self.show_filter_picker = False
        self.feedback_text = ""
        self.feedback_color = (255, 255, 255)
        self.feedback_until = 0.0
        self.final_stats = {}
        self.board_service = WeakEyeKeyBoardService()
        self.scoring = WeakEyeKeyScoringService()
        self.session = WeakEyeKeySessionService(self._session_seconds())
        self.round_data = {"keys": [], "target_index": 0, "clue": {}, "stage_index": 0}
        self.selected_index = None
        self._refresh_fonts()
        self._build_ui()

    def _refresh_fonts(self):
        self.title_font = self.create_font(54)
        self.sub_font = self.create_font(26)
        self.option_font = self.create_font(28)
        self.body_font = self.create_font(22)
        self.small_font = self.create_font(18)
        self.tiny_font = self.create_font(16)

    def _build_ui(self):
        card_w = min(560, self.width - 120)
        start_x = self.width // 2 - card_w // 2
        self.btn_start = pygame.Rect(start_x, 208, card_w, 58)
        self.btn_help = pygame.Rect(start_x, 282, card_w, 58)
        self.btn_back = pygame.Rect(self.width - 110, 18, 88, 36)
        self.btn_home = pygame.Rect(self.width - 110, 18, 88, 36)
        self.btn_confirm = pygame.Rect(self.width // 2 - 94, self.height - 62, 188, 44)
        self.btn_continue = pygame.Rect(self.width // 2 - 210, self.height - 100, 180, 48)
        self.btn_exit = pygame.Rect(self.width // 2 + 30, self.height - 100, 180, 48)
        self.help_ok = pygame.Rect(self.width // 2 - 90, self.height - 90, 180, 54)
        self.filter_modal = pygame.Rect(self.width // 2 - 250, self.height // 2 - 128, 500, 220)
        self.filter_lr = pygame.Rect(self.filter_modal.x + 24, self.filter_modal.y + 68, 210, 46)
        self.filter_rl = pygame.Rect(self.filter_modal.x + 266, self.filter_modal.y + 68, 210, 46)
        self.filter_start = pygame.Rect(self.filter_modal.centerx - 90, self.filter_modal.y + 150, 180, 44)
        self.clue_rect = pygame.Rect(76, 144, self.width - 152, 84)
        self.play_area = pygame.Rect(64, self.clue_rect.bottom + 20, self.width - 128, self.height - self.clue_rect.bottom - 118)
        self.board_rect = self.play_area.copy()

    def on_resize(self, width, height):
        self.width = width
        self.height = height
        self._build_ui()
        if self.state == self.STATE_PLAY:
            self._new_round()

    def reset(self):
        self.state = self.STATE_HOME
        self.mode = self.MODE_GLASSES
        self.filter_direction = self.FILTER_LR
        self.show_filter_picker = False
        self.feedback_text = ""
        self.final_stats = {}
        self.scoring.reset()
        self.session.session_seconds = self._session_seconds()
        self.session.reset()
        self.selected_index = None

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
        if text:
            label = self.option_font.render(text, True, text_color)
            icon = self._load_ui_icon(icon_name, light=sum(text_color) > 500) if icon_name else None
            gap = 8 if icon is not None else 0
            width = label.get_width() + (icon.get_width() + gap if icon is not None else 0)
            start_x = rect.centerx - width // 2
            if icon is not None:
                screen.blit(icon, (start_x, rect.centery - icon.get_height() // 2))
                start_x += icon.get_width() + gap
            screen.blit(label, (start_x, rect.centery - label.get_height() // 2))
        if selected:
            pygame.draw.circle(screen, (255, 250, 210), (rect.right - 18, rect.centery), 9)
            pygame.draw.circle(screen, (200, 84, 54), (rect.right - 18, rect.centery), 4)

    def _draw_filter_option(self, screen, rect, text, left_color, right_color, selected):
        self._draw_button(screen, rect, "", (244, 247, 255), text_color=(62, 72, 98), selected=selected)
        preview_rect = pygame.Rect(rect.x + 16, rect.y + 10, 56, rect.height - 20)
        left_rect = pygame.Rect(preview_rect.x, preview_rect.y, preview_rect.width // 2, preview_rect.height)
        right_rect = pygame.Rect(left_rect.right, preview_rect.y, preview_rect.width - left_rect.width, preview_rect.height)
        pygame.draw.rect(screen, left_color, left_rect, border_top_left_radius=8, border_bottom_left_radius=8)
        pygame.draw.rect(screen, right_color, right_rect, border_top_right_radius=8, border_bottom_right_radius=8)
        pygame.draw.rect(screen, (255, 255, 255), preview_rect, 2, border_radius=8)
        text_surface = self.small_font.render(text, True, (62, 72, 98))
        text_x = preview_rect.right + 16
        text_y = rect.centery - text_surface.get_height() // 2
        max_text_width = rect.right - 40 - text_x
        if text_surface.get_width() > max_text_width:
            text_surface = pygame.transform.smoothscale(text_surface, (max(1, max_text_width), text_surface.get_height()))
        screen.blit(text_surface, (text_x, text_y))

    def _draw_wrapped_text(self, screen, text, font, color, topleft, max_width, line_gap=4):
        units = text.split() if " " in text else list(text)
        if not units:
            return 0
        lines = []
        current = units[0]
        joiner = " " if " " in text else ""
        for word in units[1:]:
            candidate = f"{current}{joiner}{word}"
            if font.size(candidate)[0] <= max_width:
                current = candidate
            else:
                lines.append(current)
                current = word
        lines.append(current)
        y = topleft[1]
        for line in lines:
            surface = font.render(line, True, color)
            screen.blit(surface, (topleft[0], y))
            y += surface.get_height() + line_gap
        return y - topleft[1] - line_gap

    def _set_feedback(self, key, color):
        self.feedback_text = self.manager.t(key)
        self.feedback_color = color
        self.feedback_until = time.time() + 1.0

    def _play_sound(self, method_name):
        sound_manager = getattr(self.manager, "sound_manager", None)
        method = getattr(sound_manager, method_name, None) if sound_manager else None
        if method:
            method()

    def _stage_index(self):
        progress = min(1.0, self.session.session_elapsed / max(1, self.session.session_seconds)) if self.session.session_seconds else 0.0
        if progress < 0.34:
            return 0
        if progress < 0.67:
            return 1
        return 2

    def _new_round(self):
        stage_index = self._stage_index()
        self.round_data = self.board_service.create_round(self.board_rect, self.clue_rect, stage_index)
        self.selected_index = None
        self.session.restart_round(time.time())

    def _start_game(self):
        self.state = self.STATE_PLAY
        self.scoring.reset()
        self.session.session_seconds = self._session_seconds()
        self.session.start()
        self.feedback_text = ""
        self._new_round()

    def _finish_game(self):
        self.state = self.STATE_RESULT
        total = self.scoring.success_count + self.scoring.failure_count
        accuracy = round((self.scoring.success_count / total) * 100, 1) if total else 0.0
        self.final_stats = {
            "duration": int(self.session.session_elapsed),
            "success": self.scoring.success_count,
            "wrong": self.scoring.failure_count,
            "score": self.scoring.score,
            "accuracy": accuracy,
            "best_streak": self.scoring.best_streak,
            "avg_find_time": self.scoring.average_find_time(),
            "stage_reached": self.scoring.stage_reached + 1,
            "mode": self.mode,
            "filter_direction": self.filter_direction,
            "encouragement": self._result_encouragement(),
        }
        self._play_sound("play_completed")
        self._save_result()

    def _result_encouragement(self):
        if self.scoring.best_streak >= 5:
            return self.manager.t("weak_eye_key.result.encourage.steady")
        if self.scoring.success_count >= 8:
            return self.manager.t("weak_eye_key.result.encourage.clear")
        return self.manager.t("weak_eye_key.result.encourage.keep")

    def _save_result(self):
        data_manager = getattr(self.manager, "data_manager", None)
        if not data_manager:
            return
        total = self.scoring.success_count + self.scoring.failure_count
        data_manager.save_training_session(
            {
                "timestamp": datetime.now().isoformat(),
                "game_id": "suppression.weak_eye_key",
                "difficulty_level": 4,
                "total_questions": total,
                "correct_count": self.scoring.success_count,
                "wrong_count": self.scoring.failure_count,
                "duration_seconds": float(self.final_stats.get("duration", 0)),
                "accuracy_rate": self.final_stats.get("accuracy", 0.0),
                "training_metrics": {
                    "weak_eye_accuracy": self.final_stats.get("accuracy", 0.0),
                    "avg_find_time": self.final_stats.get("avg_find_time", 0.0),
                    "best_streak": self.scoring.best_streak,
                    "stage_reached": self.final_stats.get("stage_reached", 1),
                    "clue_match_accuracy": self.final_stats.get("accuracy", 0.0),
                },
            }
        )

    def _go_category(self):
        self.manager.set_scene("category")

    def _go_menu(self):
        self.manager.set_scene("menu")

    def _confirm_selection(self):
        if self.selected_index is None:
            self._set_feedback("weak_eye_key.feedback.select_first", (120, 146, 190))
            return
        success = self.selected_index == self.round_data["target_index"]
        if success:
            gained = self.scoring.on_success(self.session.round_elapsed, self.round_data["stage_index"])
            self._set_feedback("weak_eye_key.feedback.success", (90, 226, 132))
            self.feedback_text = f"{self.feedback_text}  +{gained}"
            self._play_sound("play_correct")
        else:
            self.scoring.on_failure()
            self._set_feedback("weak_eye_key.feedback.fail", (238, 118, 118))
            self._play_sound("play_wrong")
        self._new_round()

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

    def _draw_key(self, surface, rect, shape, teeth, color, outline=(92, 80, 64), line_only=False):
        width = 3 if line_only else 0
        draw_color = color if not line_only else outline
        if shape == "round":
            pygame.draw.circle(surface, draw_color, (rect.x + 18, rect.centery), 12, width)
            pygame.draw.circle(surface, outline, (rect.x + 18, rect.centery), 12, 2)
        elif shape == "square":
            head = pygame.Rect(rect.x + 6, rect.y + 4, 24, 24)
            pygame.draw.rect(surface, draw_color, head, width, border_radius=6)
            pygame.draw.rect(surface, outline, head, 2, border_radius=6)
        else:
            points = [(rect.x + 18, rect.y + 2), (rect.x + 32, rect.centery), (rect.x + 18, rect.bottom - 2), (rect.x + 4, rect.centery)]
            pygame.draw.polygon(surface, draw_color, points, width)
            pygame.draw.polygon(surface, outline, points, 2)
        stem = pygame.Rect(rect.x + 28, rect.y + 13, 32, 10)
        pygame.draw.rect(surface, draw_color, stem, width, border_radius=4)
        pygame.draw.rect(surface, outline, stem, 2, border_radius=4)
        for idx, tooth in enumerate(teeth):
            tooth_rect = pygame.Rect(stem.right - 14 + idx * 7, stem.bottom - 1, 5, tooth * 3)
            pygame.draw.rect(surface, draw_color, tooth_rect, width, border_radius=2)
            pygame.draw.rect(surface, outline, tooth_rect, 2, border_radius=2)

    def _draw_board(self, screen):
        neutral = pygame.Surface(self.board_rect.size, pygame.SRCALPHA)
        left = pygame.Surface(self.board_rect.size, pygame.SRCALPHA)
        right = pygame.Surface(self.board_rect.size, pygame.SRCALPHA)
        for index, item in enumerate(self.round_data["keys"]):
            local_rect = item["rect"].move(-self.board_rect.x, -self.board_rect.y)
            self._draw_key(neutral, local_rect, item["shape"], item["teeth"], (244, 242, 238), outline=(132, 122, 112))
            if index == self.selected_index:
                pygame.draw.rect(neutral, (255, 236, 156), local_rect.inflate(10, 10), 3, border_radius=12)
            if self.mode == self.MODE_GLASSES:
                if self.filter_direction == self.FILTER_LR:
                    self._draw_key(left, local_rect, item["shape"], (1, 1), item["color"], line_only=True)
                    self._draw_key(right, local_rect, "round", item["teeth"], item["color"], line_only=True)
                else:
                    self._draw_key(left, local_rect, "round", item["teeth"], item["color"], line_only=True)
                    self._draw_key(right, local_rect, item["shape"], (1, 1), item["color"], line_only=True)
        screen.blit(neutral, self.board_rect.topleft)
        if self.mode == self.MODE_GLASSES:
            screen.blit(apply_filter(left, self.mode, self.filter_direction, "left"), self.board_rect.topleft)
            screen.blit(apply_filter(right, self.mode, self.filter_direction, "right"), self.board_rect.topleft)

    def _draw_clue(self, screen):
        card = pygame.Rect(self.clue_rect.x, self.clue_rect.y, self.clue_rect.width, self.clue_rect.height)
        panel = pygame.Surface(card.size, pygame.SRCALPHA)
        panel.fill((248, 252, 255, 182))
        screen.blit(panel, card.topleft)
        pygame.draw.rect(screen, (214, 228, 244), card, 1, border_radius=14)
        title = self.small_font.render(self.manager.t("weak_eye_key.clue"), True, (70, 90, 120))
        key_rect = pygame.Rect(self.clue_rect.right - 152, self.clue_rect.y + 20, 112, 46)
        text_max_width = key_rect.left - (self.clue_rect.x + 18) - 18
        screen.blit(title, (self.clue_rect.x + 18, self.clue_rect.y + 12))
        self._draw_wrapped_text(
            screen,
            self.manager.t("weak_eye_key.clue_hint"),
            self.small_font,
            (92, 106, 130),
            (self.clue_rect.x + 18, self.clue_rect.y + 34),
            text_max_width,
            line_gap=2,
        )
        clue = self.round_data["clue"]
        local = key_rect.move(-self.clue_rect.x, -self.clue_rect.y)
        neutral = pygame.Surface(self.clue_rect.size, pygame.SRCALPHA)
        left = pygame.Surface(self.clue_rect.size, pygame.SRCALPHA)
        right = pygame.Surface(self.clue_rect.size, pygame.SRCALPHA)
        self._draw_key(neutral, local, clue["shape"], clue["teeth"], clue["color"])
        if self.mode == self.MODE_GLASSES:
            if self.filter_direction == self.FILTER_LR:
                self._draw_key(left, local, clue["shape"], (1, 1), clue["color"], line_only=True)
                self._draw_key(right, local, "round", clue["teeth"], clue["color"], line_only=True)
            else:
                self._draw_key(left, local, "round", clue["teeth"], clue["color"], line_only=True)
                self._draw_key(right, local, clue["shape"], (1, 1), clue["color"], line_only=True)
        if self.mode == self.MODE_GLASSES:
            screen.blit(apply_filter(left, self.mode, self.filter_direction, "left"), self.clue_rect.topleft)
            screen.blit(apply_filter(right, self.mode, self.filter_direction, "right"), self.clue_rect.topleft)
        else:
            screen.blit(neutral, self.clue_rect.topleft)

    def _draw_help_step(self, screen, idx, y, text):
        x = 120
        icon_center = (x + 20, y + 18)
        if idx == 1:
            pygame.draw.circle(screen, (255, 208, 124), icon_center, 14)
            pygame.draw.circle(screen, (255, 168, 126), (icon_center[0] + 20, icon_center[1]), 10)
        elif idx == 2:
            pygame.draw.circle(screen, (136, 198, 255), icon_center, 14)
            pygame.draw.circle(screen, (136, 198, 255), (icon_center[0] + 22, icon_center[1]), 14)
            pygame.draw.rect(screen, (112, 134, 170), pygame.Rect(icon_center[0] + 8, icon_center[1] - 2, 6, 4))
        else:
            pygame.draw.circle(screen, (162, 225, 162), icon_center, 14)
            pygame.draw.rect(screen, (255, 255, 255), pygame.Rect(icon_center[0] - 4, icon_center[1] - 8, 8, 16), border_radius=3)
        self._draw_wrapped_text(screen, f"{idx}. {text}", self.small_font, (58, 84, 118), (x + 52, y + 2), self.width - (x + 150), line_gap=2)

    def _draw_home(self, screen):
        title = self.title_font.render(self.manager.t("weak_eye_key.title"), True, (38, 66, 108))
        screen.blit(title, (self.width // 2 - title.get_width() // 2, 82))
        self._draw_button(screen, self.btn_start, self.manager.t("weak_eye_key.home.start"), GLASSES_BUTTON_COLOR, icon_name="target")
        self._draw_button(screen, self.btn_help, self.manager.t("weak_eye_key.home.help"), (126, 142, 174), icon_name="question")
        self._draw_button(screen, self.btn_back, self.manager.t("common.back"), (88, 116, 168), icon_name="back_arrow")
        if self.show_filter_picker:
            modal = pygame.Surface((self.filter_modal.width, self.filter_modal.height), pygame.SRCALPHA)
            modal.fill((248, 253, 255, 238))
            screen.blit(modal, self.filter_modal.topleft)
            pygame.draw.rect(screen, (116, 148, 196), self.filter_modal, 2, border_radius=12)
            title = self.body_font.render(self.manager.t("weak_eye_key.filter.pick"), True, (52, 76, 110))
            screen.blit(title, (self.filter_modal.centerx - title.get_width() // 2, self.filter_modal.y + 24))
            self._draw_filter_option(
                screen,
                self.filter_lr,
                self.manager.t("weak_eye_key.filter.lr"),
                RED_FILTER[:3],
                BLUE_FILTER[:3],
                self.filter_direction == self.FILTER_LR,
            )
            self._draw_filter_option(
                screen,
                self.filter_rl,
                self.manager.t("weak_eye_key.filter.rl"),
                BLUE_FILTER[:3],
                RED_FILTER[:3],
                self.filter_direction == self.FILTER_RL,
            )
            self._draw_button(screen, self.filter_start, self.manager.t("weak_eye_key.filter.start"), (86, 150, 108), icon_name="check")

    def _draw_help(self, screen):
        title = self.title_font.render(self.manager.t("weak_eye_key.help.title"), True, (42, 70, 110))
        deco = self.sub_font.render("?", True, (106, 136, 192))
        screen.blit(title, (self.width // 2 - title.get_width() // 2, 76))
        screen.blit(deco, (self.width // 2 + title.get_width() // 2 + 8, 86))
        screen.blit(deco, (self.width // 2 - title.get_width() // 2 - 22, 86))
        self._draw_help_step(screen, 1, 190, self.manager.t("weak_eye_key.help.step1"))
        self._draw_help_step(screen, 2, 280, self.manager.t("weak_eye_key.help.step2"))
        self._draw_help_step(screen, 3, 370, self.manager.t("weak_eye_key.help.step3"))
        self._draw_button(screen, self.help_ok, self.manager.t("weak_eye_key.help.ok"), (244, 208, 120), text_color=(92, 76, 34), icon_name="check")

    def _draw_play(self, screen):
        is_glasses_mode = self.mode == self.MODE_GLASSES
        hud_primary = (42, 12, 72) if is_glasses_mode else (55, 82, 122)
        hud_secondary = (88, 28, 92) if is_glasses_mode else (86, 104, 130)
        hud_alert = (132, 18, 32) if is_glasses_mode else (222, 74, 74)
        confirm_color = (52, 124, 82) if is_glasses_mode else (72, 148, 102)
        back_color = (62, 52, 128) if is_glasses_mode else (86, 116, 170)

        mode_text = self.manager.t("weak_eye_key.mode.glasses")
        remaining = max(0, int(self.session.session_seconds - self.session.session_elapsed))
        right_lines = ()
        left_lines = (self.manager.t(self.board_service.stage_label_key(self.round_data["stage_index"])),)
        if is_glasses_mode:
            filter_text_key = "weak_eye_key.filter.lr" if self.filter_direction == self.FILTER_LR else "weak_eye_key.filter.rl"
            left_lines = (
                self.manager.t(filter_text_key),
                self.manager.t(self.board_service.stage_label_key(self.round_data["stage_index"])),
            )
        self.draw_session_hud(
            screen,
            top_font=self.body_font,
            meta_font=self.small_font,
            left_title=mode_text,
            timer_text=self.manager.t("weak_eye_key.time", sec=f"{remaining // 60:02d}:{remaining % 60:02d}"),
            center_text=self.manager.t("weak_eye_key.score", score=self.scoring.score),
            left_lines=left_lines,
            right_lines=right_lines,
            play_area=self.play_area,
            timer_color=hud_alert if remaining <= 30 else hud_primary,
            center_color=hud_primary,
            left_title_color=hud_primary,
            meta_color=hud_secondary,
            meta_start_y=50,
        )
        board_label = self.small_font.render(self.manager.t("weak_eye_key.play.guide"), True, hud_secondary)
        screen.blit(board_label, (self.play_area.centerx - board_label.get_width() // 2, self.play_area.y + 6))

        self._draw_clue(screen)
        self._draw_board(screen)

        if self.feedback_text and time.time() <= self.feedback_until:
            feedback = self.body_font.render(self.feedback_text, True, self.feedback_color)
            screen.blit(feedback, (self.width // 2 - feedback.get_width() // 2, self.play_area.bottom - 12))

        self._draw_button(screen, self.btn_confirm, self.manager.t("weak_eye_key.confirm"), confirm_color, icon_name="check")
        self._draw_button(screen, self.btn_home, self.manager.t("common.back"), back_color, icon_name="back_arrow")

    def _draw_result(self, screen):
        title = self.title_font.render(self.manager.t("weak_eye_key.result.title"), True, (42, 70, 110))
        screen.blit(title, (self.width // 2 - title.get_width() // 2, 100))
        mode_text = self.manager.t("weak_eye_key.mode.glasses")
        filter_text = "-"
        if self.final_stats.get("mode") == self.MODE_GLASSES:
            filter_text = self.manager.t("weak_eye_key.filter.lr") if self.final_stats.get("filter_direction") == self.FILTER_LR else self.manager.t("weak_eye_key.filter.rl")
        lines = [
            (self.manager.t("weak_eye_key.result.duration", sec=self.final_stats.get("duration", 0)), (58, 84, 118)),
            (self.manager.t("weak_eye_key.result.success", n=self.final_stats.get("success", 0)), (58, 84, 118)),
            (self.manager.t("weak_eye_key.result.wrong", n=self.final_stats.get("wrong", 0)), (58, 84, 118)),
            (self.manager.t("weak_eye_key.result.accuracy", value=self.final_stats.get("accuracy", 0.0)), (58, 84, 118)),
            (self.manager.t("weak_eye_key.result.score", n=self.final_stats.get("score", 0)), (58, 84, 118)),
            (self.manager.t("weak_eye_key.result.streak", n=self.final_stats.get("best_streak", 0)), (58, 84, 118)),
            (self.manager.t("weak_eye_key.result.find_time", sec=self.final_stats.get("avg_find_time", 0.0)), (58, 84, 118)),
            (self.manager.t("weak_eye_key.result.mode", mode=mode_text), (96, 114, 138)),
            (self.manager.t("weak_eye_key.result.filter", direction=filter_text), (96, 114, 138)),
        ]
        self.draw_two_column_stats(
            screen,
            font=self.body_font,
            entries=lines,
            top_y=184,
            left_x=self.width // 2 - 320,
            right_x=self.width // 2 + 24,
            column_width=296,
            rows_per_column=5,
            row_gap=38,
        )
        encouragement = self.body_font.render(self.final_stats.get("encouragement", ""), True, (88, 118, 82))
        screen.blit(encouragement, (self.width // 2 - encouragement.get_width() // 2, 390))
        self._draw_button(screen, self.btn_continue, self.manager.t("weak_eye_key.result.continue"), (84, 148, 108), icon_name="check")
        self._draw_button(screen, self.btn_exit, self.manager.t("weak_eye_key.result.exit"), (120, 134, 168), icon_name="cross")

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
                continue
            if self.state == self.STATE_HOME:
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        self._go_category()
                    elif event.key == pygame.K_1:
                        self.show_filter_picker = True
                    elif event.key == pygame.K_2:
                        self.state = self.STATE_HELP
                elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    pos = getattr(event, "pos", pygame.mouse.get_pos())
                    if self.btn_back.collidepoint(pos):
                        self._go_category()
                    elif self.btn_start.collidepoint(pos):
                        self.show_filter_picker = True
                    elif self.btn_help.collidepoint(pos):
                        self.state = self.STATE_HELP
            elif self.state == self.STATE_HELP:
                if event.type == pygame.KEYDOWN and event.key in (pygame.K_ESCAPE, pygame.K_RETURN):
                    self.state = self.STATE_HOME
                elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1 and self.help_ok.collidepoint(getattr(event, "pos", pygame.mouse.get_pos())):
                    self.state = self.STATE_HOME
            elif self.state == self.STATE_PLAY:
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        self._go_menu()
                    elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
                        self._confirm_selection()
                elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    pos = getattr(event, "pos", pygame.mouse.get_pos())
                    if self.btn_home.collidepoint(pos):
                        self._go_menu()
                    elif self.btn_confirm.collidepoint(pos):
                        self._confirm_selection()
                    else:
                        _success, index = self.board_service.is_target_hit(self.round_data, pos)
                        if index is not None:
                            self.selected_index = index
                            self._set_feedback("weak_eye_key.feedback.selected", (96, 156, 214))
            else:
                if event.type == pygame.KEYDOWN:
                    if event.key in (pygame.K_RETURN, pygame.K_SPACE):
                        self.reset()
                    elif event.key == pygame.K_ESCAPE:
                        self._go_menu()
                elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    pos = getattr(event, "pos", pygame.mouse.get_pos())
                    if self.btn_continue.collidepoint(pos):
                        self.reset()
                    elif self.btn_exit.collidepoint(pos):
                        self._go_menu()

    def update(self):
        now = time.time()
        if self.state == self.STATE_PLAY:
            self.session.tick(now)
            if self.session.is_complete():
                self._finish_game()
                return
            if self.session.is_round_timeout():
                self.scoring.on_failure()
                self._set_feedback("weak_eye_key.feedback.timeout", (238, 118, 118))
                self._play_sound("play_wrong")
                self._new_round()
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
