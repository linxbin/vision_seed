import time
from datetime import datetime

import pygame

from core.base_scene import BaseScene
from games.common.anaglyph import BLUE_FILTER, FILTER_LR, FILTER_RL, GLASSES_BACKGROUND, GLASSES_BUTTON_COLOR, MODE_GLASSES, RED_FILTER, apply_filter
from ..services import FindSameBoardService, FindSameScoringService, FindSameSessionService


class FindSameScene(BaseScene):
    STATE_HOME = "home"
    STATE_HELP = "help"
    STATE_PLAY = "play"
    STATE_RESULT = "result"
    MODE_NAKED = "naked"
    MODE_GLASSES = MODE_GLASSES

    def __init__(self, manager):
        super().__init__(manager)
        self.width = 900
        self.height = 700
        self.state = self.STATE_HOME
        self.mode = self.MODE_NAKED
        self.filter_direction = FILTER_LR
        self.show_filter_picker = False
        self.selected_index = 0
        self.pending_indices = set()
        self.feedback_text = ""
        self.feedback_color = (255, 255, 255)
        self.feedback_until = 0.0
        self.failure_count = 0
        self.final_stats = {}
        self.round_started_at = 0.0
        self.round_flash_until = 0.0
        self.board_service = FindSameBoardService()
        self.scoring = FindSameScoringService()
        self.session = FindSameSessionService(self._session_seconds())
        self.round_data = {"left": [], "right": [], "match_indices": []}
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
        self.btn_naked = pygame.Rect(start_x, 210, card_w, 58)
        self.btn_glasses = pygame.Rect(start_x, 284, card_w, 58)
        self.btn_help = pygame.Rect(start_x, 358, card_w, 58)
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

    def on_resize(self, width, height):
        self.width = width
        self.height = height
        self._build_ui()
        self._new_round()

    def reset(self):
        size = self.manager.screen_size or (self.width, self.height)
        self.__init__(self.manager)
        self.on_resize(*size)

    def _session_seconds(self):
        try:
            minutes = int(self.manager.settings.get("session_duration_minutes", 5))
        except (TypeError, ValueError):
            minutes = 5
        return max(60, minutes * 60)

    def _match_count(self):
        progress = min(1.0, self.session.session_elapsed / max(1, self._session_seconds())) if self.state == self.STATE_PLAY else 0.0
        return 2 if progress < 0.34 else 3 if progress < 0.67 else 4

    def _new_round(self):
        self.pending_indices = set()
        self.round_data = self.board_service.create_round(self.left_panel, self._match_count())
        self.selected_index = min(self.selected_index, len(self.round_data["right"]) - 1)
        self.round_started_at = time.time()

    def _start_game(self):
        self.state = self.STATE_PLAY
        self.scoring.reset()
        self.failure_count = 0
        self.session.session_seconds = self._session_seconds()
        self.session.start()
        self.feedback_text = ""
        self.selected_index = 0
        self._new_round()

    def _save_result(self):
        data_manager = getattr(self.manager, "data_manager", None)
        if data_manager:
            total = self.scoring.success_count + self.failure_count
            data_manager.save_training_session({
                "timestamp": datetime.now().isoformat(),
                "game_id": "suppression.find_same",
                "difficulty_level": 3,
                "total_questions": total,
                "correct_count": self.scoring.success_count,
                "wrong_count": self.failure_count,
                "duration_seconds": float(self.final_stats.get("duration", 0)),
                "accuracy_rate": self.final_stats.get("accuracy", 0.0),
                "training_metrics": {
                    "weak_eye_accuracy": self.final_stats.get("accuracy", 0.0),
                    "best_combo": self.scoring.best_combo,
                    "avg_find_time": self.final_stats.get("avg_find_time", 0.0),
                },
            })

    def _finish_game(self):
        total = self.scoring.success_count + self.failure_count
        accuracy = round((self.scoring.success_count / total) * 100, 1) if total else 0.0
        self.final_stats = {"duration": int(self.session.session_elapsed), "success": self.scoring.success_count, "wrong": self.failure_count, "score": self.scoring.score, "accuracy": accuracy, "avg_find_time": self.scoring.average_reaction_time(), "best_combo": self.scoring.best_combo}
        self.state = self.STATE_RESULT
        self.play_completed_sound()
        self._save_result()

    def _set_feedback(self, key, color):
        self.feedback_text = self.manager.t(key)
        self.feedback_color = color
        self.feedback_until = time.time() + 1.0

    def _draw_button(self, screen, rect, text, color, text_color=(255, 255, 255), selected=False):
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
        screen.blit(label, (rect.centerx - label.get_width() // 2, rect.centery - label.get_height() // 2))
        if selected:
            pygame.draw.circle(screen, (255, 250, 210), (rect.right - 18, rect.centery), 9)
            pygame.draw.circle(screen, (200, 84, 54), (rect.right - 18, rect.centery), 4)

    def _draw_wrapped(self, screen, text, x, y, width):
        units = text.split() if " " in text else list(text)
        line = ""
        yy = y
        for unit in units:
            candidate = f"{line} {unit}".strip() if " " in text else f"{line}{unit}"
            if line and self.body_font.size(candidate)[0] > width:
                surf = self.body_font.render(line, True, (72, 90, 116))
                screen.blit(surf, (x, yy))
                yy += surf.get_height() + 4
                line = unit
            else:
                line = candidate
        if line:
            surf = self.body_font.render(line, True, (72, 90, 116))
            screen.blit(surf, (x, yy))

    def _draw_background(self, screen):
        for y in range(self.height):
            t = y / max(1, self.height - 1)
            color = (int(232 * (1 - t) + 220 * t), int(245 * (1 - t) + 238 * t), int(255 * (1 - t) + 252 * t))
            pygame.draw.line(screen, color, (0, y), (self.width, y))
        if self.state == self.STATE_PLAY and self.mode == self.MODE_GLASSES:
            overlay = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
            overlay.fill(GLASSES_BACKGROUND)
            screen.blit(overlay, (0, 0))

    def _draw_boards(self, screen):
        left_surface = pygame.Surface(self.left_panel.size, pygame.SRCALPHA)
        right_surface = pygame.Surface(self.right_panel.size, pygame.SRCALPHA)
        for item in self.round_data["left"]:
            self.board_service.draw_shape(left_surface, item["shape"], item["center"], item["size"], item["color"], outline_color=(42, 54, 76, 92), outline_width=2)
        for index, item in enumerate(self.round_data["right"]):
            self.board_service.draw_shape(right_surface, item["shape"], item["center"], item["size"], item["color"], outline_color=(42, 54, 76, 92), outline_width=2)
            if index in self.pending_indices or index == self.selected_index:
                rect = pygame.Rect(0, 0, item["size"] + 22, item["size"] + 22)
                rect.center = item["center"]
                pygame.draw.rect(right_surface, (96, 156, 214, 220) if index in self.pending_indices else (255, 239, 152, 210), rect, 3, border_radius=10)
        if self.mode == self.MODE_GLASSES:
            left_surface = apply_filter(left_surface, self.mode, self.filter_direction, "left")
            right_surface = apply_filter(right_surface, self.mode, self.filter_direction, "right")
        screen.blit(left_surface, self.left_panel.topleft)
        screen.blit(right_surface, self.right_panel.topleft)
        for label, panel in ((self.manager.t("find_same.panel.left"), self.left_panel), (self.manager.t("find_same.panel.right"), self.right_panel)):
            surf = self.small_font.render(label, True, (78, 96, 124))
            screen.blit(surf, (panel.centerx - surf.get_width() // 2, panel.y - 28))

    def _draw_home(self, screen):
        title = self.title_font.render(self.manager.t("find_same.title"), True, (34, 60, 96))
        subtitle = self.sub_font.render(self.manager.t("find_same.subtitle"), True, (86, 104, 130))
        screen.blit(title, (self.width // 2 - title.get_width() // 2, 84))
        screen.blit(subtitle, (self.width // 2 - subtitle.get_width() // 2, 140))
        self._draw_button(screen, self.btn_naked, self.manager.t("find_same.home.naked"), (96, 140, 214))
        self._draw_button(screen, self.btn_glasses, self.manager.t("find_same.home.glasses"), GLASSES_BUTTON_COLOR)
        self._draw_button(screen, self.btn_help, self.manager.t("find_same.home.help"), (124, 140, 168))
        self._draw_button(screen, self.btn_back, self.manager.t("common.back"), (86, 116, 170))

    def _draw_help(self, screen):
        title = self.title_font.render(self.manager.t("find_same.help.title"), True, (34, 60, 96))
        screen.blit(title, (self.width // 2 - title.get_width() // 2, 68))
        steps = [self.manager.t("find_same.help.step1"), self.manager.t("find_same.help.step2"), self.manager.t("find_same.help.step3")]
        for idx, text in enumerate(steps):
            card = pygame.Rect(90, 156 + idx * 106, self.width - 180, 94)
            pygame.draw.rect(screen, (246, 250, 255), card, border_radius=18)
            pygame.draw.rect(screen, (196, 212, 234), card, 2, border_radius=18)
            self._draw_wrapped(screen, f"{idx + 1}. {text}", card.x + 26, card.y + 18, card.width - 52)
        self._draw_button(screen, self.help_ok, self.manager.t("find_same.help.ok"), (244, 208, 120), text_color=(92, 76, 34))

    def _draw_filter_picker(self, screen):
        overlay = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        overlay.fill((24, 32, 46, 136))
        screen.blit(overlay, (0, 0))
        pygame.draw.rect(screen, (249, 251, 255), self.filter_modal, border_radius=18)
        title = self.sub_font.render(self.manager.t("find_same.filter.pick"), True, (52, 70, 100))
        screen.blit(title, (self.filter_modal.centerx - title.get_width() // 2, self.filter_modal.y + 20))
        self._draw_filter_option(screen, self.filter_lr, self.manager.t("find_same.filter.lr"), RED_FILTER[:3], BLUE_FILTER[:3], self.filter_direction == FILTER_LR)
        self._draw_filter_option(screen, self.filter_rl, self.manager.t("find_same.filter.rl"), BLUE_FILTER[:3], RED_FILTER[:3], self.filter_direction == FILTER_RL)
        self._draw_button(screen, self.filter_start, self.manager.t("find_same.filter.start"), (92, 152, 114))

    def _draw_filter_option(self, screen, rect, text, left_color, right_color, selected):
        self._draw_button(screen, rect, "", (244, 247, 255), text_color=(62, 72, 98), selected=selected)
        preview_rect = pygame.Rect(rect.x + 16, rect.y + 10, 56, rect.height - 20)
        left_rect = pygame.Rect(preview_rect.x, preview_rect.y, preview_rect.width // 2, preview_rect.height)
        right_rect = pygame.Rect(left_rect.right, preview_rect.y, preview_rect.width - left_rect.width, preview_rect.height)
        pygame.draw.rect(screen, left_color, left_rect, border_top_left_radius=8, border_bottom_left_radius=8)
        pygame.draw.rect(screen, right_color, right_rect, border_top_right_radius=8, border_bottom_right_radius=8)
        pygame.draw.rect(screen, (255, 255, 255) if selected else (190, 206, 228), preview_rect, 2, border_radius=8)
        label = self.small_font.render(text, True, (62, 72, 98))
        screen.blit(label, (preview_rect.right + 16, rect.centery - label.get_height() // 2))

    def _draw_play(self, screen):
        remaining = len(self.round_data["match_indices"])
        timer = self.body_font.render(self.manager.t("find_same.time", sec=f"{max(0, int(self._session_seconds() - self.session.session_elapsed)) // 60:02d}:{max(0, int(self._session_seconds() - self.session.session_elapsed)) % 60:02d}"), True, (86, 116, 170))
        score = self.body_font.render(self.manager.t("find_same.score", score=self.scoring.score), True, (44, 60, 88))
        combo = self.body_font.render(self.manager.t("find_same.combo", combo=self.scoring.best_combo), True, (92, 102, 120))
        target = self.body_font.render(self.manager.t("find_same.target", remaining=remaining), True, (88, 72, 32))
        tip = self.small_font.render(self.manager.t("find_same.play.guide"), True, (54, 70, 96))
        screen.blit(timer, (self.width // 2 - timer.get_width() // 2, 18))
        screen.blit(score, (84, 22))
        screen.blit(combo, (self.width - 124 - combo.get_width(), 26))
        screen.blit(target, (84, 58))
        screen.blit(tip, (self.width // 2 - tip.get_width() // 2, 98))
        self._draw_button(screen, self.btn_home, self.manager.t("common.back"), (86, 116, 170))
        self._draw_boards(screen)
        divider_x = self.left_panel.right + (self.right_panel.left - self.left_panel.right) // 2
        for y in range(self.left_panel.y + 8, self.left_panel.bottom - 8, 18):
            pygame.draw.line(screen, (196, 210, 230), (divider_x, y), (divider_x, min(y + 10, self.left_panel.bottom - 8)), 3)
        if self.feedback_text:
            fb = self.option_font.render(self.feedback_text, True, self.feedback_color)
            screen.blit(fb, (self.width // 2 - fb.get_width() // 2, self.height - 122))
        self._draw_button(screen, self.btn_confirm, self.manager.t("find_same.confirm"), (84, 148, 108))

    def _draw_result(self, screen):
        title = self.title_font.render(self.manager.t("find_same.result.title"), True, (34, 60, 96))
        screen.blit(title, (self.width // 2 - title.get_width() // 2, 80))
        lines = [
            self.manager.t("find_same.result.duration", sec=self.final_stats.get("duration", 0)),
            self.manager.t("find_same.result.success", n=self.final_stats.get("success", 0)),
            self.manager.t("find_same.result.wrong", n=self.final_stats.get("wrong", 0)),
            self.manager.t("find_same.result.accuracy", value=self.final_stats.get("accuracy", 0.0)),
            self.manager.t("find_same.result.score", n=self.final_stats.get("score", 0)),
            self.manager.t("find_same.result.avg_find_time", sec=self.final_stats.get("avg_find_time", 0.0)),
            self.manager.t("find_same.result.combo", n=self.final_stats.get("best_combo", 0)),
        ]
        for idx, text in enumerate(lines):
            surf = self.body_font.render(text, True, (66, 84, 114))
            screen.blit(surf, (self.width // 2 - surf.get_width() // 2, 176 + idx * 36))
        self._draw_button(screen, self.btn_continue, self.manager.t("find_same.result.continue"), (84, 148, 108))
        self._draw_button(screen, self.btn_exit, self.manager.t("find_same.result.exit"), (120, 134, 168))

    def handle_events(self, events):
        for event in events:
            if self.show_filter_picker:
                if event.type == pygame.KEYDOWN and event.key in (pygame.K_LEFT, pygame.K_RIGHT):
                    self.filter_direction = FILTER_RL if self.filter_direction == FILTER_LR else FILTER_LR
                elif event.type == pygame.KEYDOWN and event.key in (pygame.K_RETURN, pygame.K_SPACE):
                    self.show_filter_picker = False
                    self._start_game()
                elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    pos = getattr(event, "pos", pygame.mouse.get_pos())
                    if self.filter_lr.collidepoint(pos):
                        self.filter_direction = FILTER_LR
                    elif self.filter_rl.collidepoint(pos):
                        self.filter_direction = FILTER_RL
                    elif self.filter_start.collidepoint(pos):
                        self.show_filter_picker = False
                        self._start_game()
            elif self.state == self.STATE_HOME:
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
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
                        self.manager.set_scene("category")
            elif self.state == self.STATE_HELP:
                if event.type == pygame.KEYDOWN and event.key in (pygame.K_ESCAPE, pygame.K_RETURN, pygame.K_SPACE):
                    self.state = self.STATE_HOME
                elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1 and self.help_ok.collidepoint(getattr(event, "pos", pygame.mouse.get_pos())):
                    self.state = self.STATE_HOME
            elif self.state == self.STATE_PLAY:
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_LEFT:
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
                    elif event.key == pygame.K_ESCAPE:
                        self.manager.set_scene("category")
                elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    pos = getattr(event, "pos", pygame.mouse.get_pos())
                    if self.btn_home.collidepoint(pos):
                        self.manager.set_scene("category")
                    elif self.btn_confirm.collidepoint(pos):
                        self._confirm_selection()
                    else:
                        for idx, item in enumerate(self.round_data["right"]):
                            center = (self.right_panel.x + item["center"][0], self.right_panel.y + item["center"][1])
                            if self.board_service.hit_test_shape(item["shape"], center, item["size"], pos):
                                self.selected_index = idx
                                self._toggle_pending_selection(idx)
                                break
            else:
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    pos = getattr(event, "pos", pygame.mouse.get_pos())
                    if self.btn_continue.collidepoint(pos):
                        self.state = self.STATE_HOME
                    elif self.btn_exit.collidepoint(pos):
                        self.manager.set_scene("menu")

    def _confirm_selection(self):
        if self.pending_indices == set(self.round_data["match_indices"]):
            reaction_time = time.time() - self.round_started_at if self.round_started_at > 0 else None
            for _ in self.pending_indices:
                self.scoring.on_success(reaction_time)
            self.play_correct_sound()
            self.pending_indices.clear()
            self.round_flash_until = time.time() + 0.2
            self._set_feedback("find_same.feedback.round_clear", (90, 226, 132))
            self._new_round()
        else:
            self.scoring.on_failure()
            self.failure_count += 1
            self.play_wrong_sound()
            self.pending_indices.clear()
            self._set_feedback("find_same.feedback.fail", (238, 118, 118))

    def _toggle_pending_selection(self, index):
        if index in self.pending_indices:
            self.pending_indices.remove(index)
            if self.selected_index == index:
                self.selected_index = -1
            self._set_feedback("find_same.feedback.unselect", (130, 146, 188))
        else:
            self.pending_indices.add(index)
            self.selected_index = index
            self._set_feedback("find_same.feedback.select", (96, 156, 214))

    def update(self):
        now = time.time()
        if self.state == self.STATE_PLAY:
            self.session.tick(now)
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
