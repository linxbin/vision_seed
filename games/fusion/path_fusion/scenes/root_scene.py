import time
from datetime import datetime

import pygame

from core.base_scene import BaseScene
from games.common.anaglyph import BLUE_FILTER, FILTER_LR, FILTER_RL, GLASSES_BACKGROUND, GLASSES_BUTTON_COLOR, MODE_GLASSES, RED_FILTER
from ..services import PathFusionBoardService, PathFusionScoringService, PathFusionSessionService


class PathFusionScene(BaseScene):
    STATE_HOME = "home"
    STATE_HELP = "help"
    STATE_PLAY = "play"
    STATE_RESULT = "result"
    MODE_NAKED = "naked"
    MODE_GLASSES = MODE_GLASSES
    GLASSES_PATH_OFFSET = 8

    def __init__(self, manager):
        super().__init__(manager)
        self.width = 900
        self.height = 700
        self.state = self.STATE_HOME
        self.mode = self.MODE_NAKED
        self.filter_direction = FILTER_LR
        self.show_filter_picker = False
        self.feedback_text = ""
        self.feedback_color = (255, 255, 255)
        self.feedback_until = 0.0
        self.final_stats = {}
        self.board_service = PathFusionBoardService()
        self.scoring = PathFusionScoringService()
        self.session = PathFusionSessionService(self._session_seconds())
        self.round_data = {}
        self.selected_path = 0
        self._refresh_fonts()
        self._build_ui()

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
        self.btn_continue = pygame.Rect(self.width // 2 - 210, self.height - 100, 180, 48)
        self.btn_exit = pygame.Rect(self.width // 2 + 30, self.height - 100, 180, 48)
        self.help_ok = pygame.Rect(self.width // 2 - 90, self.height - 90, 180, 54)
        self.filter_modal = pygame.Rect(self.width // 2 - 250, self.height // 2 - 128, 500, 220)
        self.filter_lr = pygame.Rect(self.filter_modal.x + 24, self.filter_modal.y + 68, 210, 46)
        self.filter_rl = pygame.Rect(self.filter_modal.x + 266, self.filter_modal.y + 68, 210, 46)
        self.filter_start = pygame.Rect(self.filter_modal.centerx - 90, self.filter_modal.y + 150, 180, 44)
        option_y = self.height - 150
        self.option_rects = [
            pygame.Rect(self.width // 2 - 210, option_y, 120, 44),
            pygame.Rect(self.width // 2 - 60, option_y, 120, 44),
            pygame.Rect(self.width // 2 + 90, option_y, 120, 44),
        ]

    def on_resize(self, width, height):
        self.width = width
        self.height = height
        self._build_ui()

    def _session_seconds(self):
        try:
            minutes = int(self.manager.settings.get("session_duration_minutes", 5))
        except (TypeError, ValueError):
            minutes = 5
        return max(60, minutes * 60)

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

    def _draw_wrapped_text(self, screen, text, x, y, max_width):
        units = text.split() if " " in text else list(text)
        line = ""
        current_y = y
        joiner = " " if " " in text else ""
        for unit in units:
            candidate = f"{line}{joiner}{unit}" if line else unit
            if line and self.body_font.size(candidate)[0] > max_width:
                surf = self.body_font.render(line, True, (58, 84, 118))
                screen.blit(surf, (x, current_y))
                current_y += surf.get_height() + 4
                line = unit
            else:
                line = candidate
        if line:
            surf = self.body_font.render(line, True, (58, 84, 118))
            screen.blit(surf, (x, current_y))

    def _draw_background(self, screen):
        top = (236, 244, 255)
        bottom = (221, 235, 250)
        for y in range(self.height):
            t = y / max(1, self.height - 1)
            color = (int(top[0] * (1 - t) + bottom[0] * t), int(top[1] * (1 - t) + bottom[1] * t), int(top[2] * (1 - t) + bottom[2] * t))
            pygame.draw.line(screen, color, (0, y), (self.width, y))
        if self.state == self.STATE_PLAY and self.mode == self.MODE_GLASSES:
            overlay = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
            overlay.fill(GLASSES_BACKGROUND)
            screen.blit(overlay, (0, 0))

    def _new_round(self):
        self.round_data = self.board_service.create_round()
        self.selected_path = 0

    def _start_game(self):
        self.state = self.STATE_PLAY
        self.scoring.reset()
        self.session.session_seconds = self._session_seconds()
        self.session.start()
        self._new_round()

    def _save_result(self):
        if getattr(self.manager, "data_manager", None):
            self.manager.data_manager.save_training_session({
                "timestamp": datetime.now().isoformat(),
                "game_id": "fusion.path_fusion",
                "difficulty_level": 3,
                "total_questions": self.scoring.success_count + self.scoring.failure_count,
                "correct_count": self.scoring.success_count,
                "wrong_count": self.scoring.failure_count,
                "duration_seconds": float(self.final_stats.get("duration", 0)),
                "accuracy_rate": self.final_stats.get("accuracy", 0.0),
                "training_metrics": {
                    "fusion_path_accuracy": self.final_stats.get("accuracy", 0.0),
                    "best_streak": 0,
                    "avg_solve_time": 0.0,
                },
            })

    def _finish_game(self):
        self.final_stats = {
            "duration": int(self.session.session_elapsed),
            "success": self.scoring.success_count,
            "wrong": self.scoring.failure_count,
            "accuracy": self.scoring.accuracy(),
            "score": self.scoring.score,
        }
        self.state = self.STATE_RESULT
        self.play_completed_sound()
        self._save_result()

    def _set_feedback(self, key, color):
        self.feedback_text = self.manager.t(key)
        self.feedback_color = color
        self.feedback_until = time.time() + 0.8

    def _glasses_colors(self):
        if self.filter_direction == FILTER_LR:
            return RED_FILTER[:3], BLUE_FILTER[:3]
        return BLUE_FILTER[:3], RED_FILTER[:3]

    def _draw_filter_picker(self, screen):
        overlay = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        overlay.fill((24, 32, 46, 136))
        screen.blit(overlay, (0, 0))
        pygame.draw.rect(screen, (249, 251, 255), self.filter_modal, border_radius=18)
        title = self.sub_font.render(self.manager.t("path_fusion.filter.pick"), True, (52, 70, 100))
        screen.blit(title, (self.filter_modal.centerx - title.get_width() // 2, self.filter_modal.y + 20))
        for rect, text, left, right, selected in (
            (self.filter_lr, self.manager.t("path_fusion.filter.lr"), RED_FILTER[:3], BLUE_FILTER[:3], self.filter_direction == FILTER_LR),
            (self.filter_rl, self.manager.t("path_fusion.filter.rl"), BLUE_FILTER[:3], RED_FILTER[:3], self.filter_direction == FILTER_RL),
        ):
            self._draw_button(screen, rect, "", (244, 247, 255), text_color=(62, 72, 98), selected=selected)
            preview_rect = pygame.Rect(rect.x + 16, rect.y + 10, 56, rect.height - 20)
            pygame.draw.rect(screen, left, pygame.Rect(preview_rect.x, preview_rect.y, preview_rect.width // 2, preview_rect.height), border_top_left_radius=8, border_bottom_left_radius=8)
            pygame.draw.rect(screen, right, pygame.Rect(preview_rect.centerx, preview_rect.y, preview_rect.width // 2, preview_rect.height), border_top_right_radius=8, border_bottom_right_radius=8)
            pygame.draw.rect(screen, (255, 255, 255) if selected else (190, 206, 228), preview_rect, 2, border_radius=8)
            label = self.small_font.render(text, True, (62, 72, 98))
            screen.blit(label, (preview_rect.right + 16, rect.centery - label.get_height() // 2))
        self._draw_button(screen, self.filter_start, self.manager.t("path_fusion.filter.start"), (92, 152, 114))

    def _draw_home(self, screen):
        title = self.title_font.render(self.manager.t("path_fusion.title"), True, (34, 60, 96))
        screen.blit(title, (self.width // 2 - title.get_width() // 2, 82))
        self._draw_button(screen, self.btn_naked, self.manager.t("path_fusion.home.naked"), (96, 140, 214))
        self._draw_button(screen, self.btn_glasses, self.manager.t("path_fusion.home.glasses"), GLASSES_BUTTON_COLOR)
        self._draw_button(screen, self.btn_help, self.manager.t("path_fusion.home.help"), (124, 140, 168))
        self._draw_button(screen, self.btn_back, self.manager.t("common.back"), (86, 116, 170))

    def _draw_help(self, screen):
        title = self.title_font.render(self.manager.t("path_fusion.help.title"), True, (34, 60, 96))
        screen.blit(title, (self.width // 2 - title.get_width() // 2, 76))
        for idx, key in enumerate(("path_fusion.help.step1", "path_fusion.help.step2", "path_fusion.help.step3")):
            card = pygame.Rect(90, 170 + idx * 104, self.width - 180, 88)
            pygame.draw.rect(screen, (246, 250, 255), card, border_radius=16)
            pygame.draw.rect(screen, (196, 212, 234), card, 2, border_radius=16)
            self._draw_wrapped_text(screen, f"{idx + 1}. {self.manager.t(key)}", card.x + 20, card.y + 16, card.width - 40)
        self._draw_button(screen, self.help_ok, self.manager.t("path_fusion.help.ok"), (244, 208, 120), text_color=(92, 76, 34))

    def _draw_play(self, screen):
        remaining = max(0, int(self.session.session_seconds - self.session.session_elapsed))
        timer = self.body_font.render(self.manager.t("path_fusion.time", sec=f"{remaining // 60:02d}:{remaining % 60:02d}"), True, (86, 116, 170))
        score = self.body_font.render(self.manager.t("path_fusion.score", score=self.scoring.score), True, (44, 60, 88))
        mode = self.body_font.render(self.manager.t("path_fusion.mode.glasses" if self.mode == self.MODE_GLASSES else "path_fusion.mode.naked"), True, (44, 60, 88))
        guide = self.small_font.render(self.manager.t("path_fusion.play.guide"), True, (54, 70, 96))
        screen.blit(mode, (self.width - mode.get_width() - 126, 18))
        screen.blit(timer, (self.width // 2 - timer.get_width() // 2, 18))
        screen.blit(score, (84, 22))
        screen.blit(guide, (self.width // 2 - guide.get_width() // 2, 98))
        board = pygame.Rect(self.width // 2 - 220, 160, 440, 260)
        pygame.draw.rect(screen, (246, 250, 255), board, border_radius=14)
        pygame.draw.rect(screen, (190, 206, 228), board, 2, border_radius=14)
        start = (board.x + 90, board.y + 80)
        mid = (board.centerx, board.centery)
        target_points = [(board.right - 90, board.y + 70), (board.right - 90, board.centery), (board.right - 90, board.bottom - 70)]
        if self.mode == self.MODE_GLASSES:
            left_color, right_color = self._glasses_colors()
            left_start = (start[0] - self.GLASSES_PATH_OFFSET, start[1])
            left_mid = (mid[0] - self.GLASSES_PATH_OFFSET, mid[1])
            right_mid = (mid[0] + self.GLASSES_PATH_OFFSET, mid[1])
            pygame.draw.circle(screen, left_color, left_start, 10)
            pygame.draw.line(screen, left_color, left_start, left_mid, 5)
            for idx, point in enumerate(target_points):
                right_point = (point[0] + self.GLASSES_PATH_OFFSET, point[1])
                pygame.draw.circle(screen, right_color, right_point, 12, 3)
                pygame.draw.line(screen, right_color, right_mid, right_point, 5 if idx == self.selected_path else 3)
            for idx, point in enumerate(target_points):
                outline_color = (38, 42, 52) if idx == self.round_data["target"] else (124, 134, 152)
                pygame.draw.circle(screen, outline_color, point, 8 if idx == self.round_data["target"] else 6)
                pygame.draw.circle(screen, (248, 250, 252), point, 3 if idx == self.round_data["target"] else 2)
            pygame.draw.circle(screen, (66, 84, 114), start, 5)
            pygame.draw.circle(screen, (66, 84, 114), mid, 5)
        else:
            pygame.draw.circle(screen, (82, 130, 232), start, 10)
            for idx, point in enumerate(target_points):
                pygame.draw.circle(screen, (232, 78, 78) if idx == self.round_data["target"] else (180, 188, 204), point, 12, 3)
                pygame.draw.line(screen, (96, 140, 214) if idx == self.selected_path else (154, 170, 196), mid, point, 5)
            pygame.draw.line(screen, (154, 170, 196), start, mid, 5)
        for idx, rect in enumerate(self.option_rects):
            self._draw_button(screen, rect, str(idx + 1), (96, 140, 214) if idx == self.selected_path else (124, 140, 168))
        if self.feedback_text and time.time() <= self.feedback_until:
            fb = self.option_font.render(self.feedback_text, True, self.feedback_color)
            screen.blit(fb, (self.width // 2 - fb.get_width() // 2, board.bottom + 20))
        self._draw_button(screen, self.btn_home, self.manager.t("common.back"), (86, 116, 170))

    def _draw_result(self, screen):
        title = self.title_font.render(self.manager.t("path_fusion.result.title"), True, (34, 60, 96))
        screen.blit(title, (self.width // 2 - title.get_width() // 2, 84))
        lines = [
            self.manager.t("path_fusion.result.duration", sec=self.final_stats.get("duration", 0)),
            self.manager.t("path_fusion.result.success", n=self.final_stats.get("success", 0)),
            self.manager.t("path_fusion.result.wrong", n=self.final_stats.get("wrong", 0)),
            self.manager.t("path_fusion.result.accuracy", value=self.final_stats.get("accuracy", 0.0)),
            self.manager.t("path_fusion.result.score", n=self.final_stats.get("score", 0)),
        ]
        for idx, text in enumerate(lines):
            line = self.body_font.render(text, True, (66, 84, 114))
            screen.blit(line, (self.width // 2 - line.get_width() // 2, 176 + idx * 34))
        self._draw_button(screen, self.btn_continue, self.manager.t("path_fusion.result.continue"), (84, 148, 108))
        self._draw_button(screen, self.btn_exit, self.manager.t("path_fusion.result.exit"), (120, 134, 168))

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
                if event.type == pygame.KEYDOWN and event.key in (pygame.K_ESCAPE, pygame.K_RETURN):
                    self.state = self.STATE_HOME
                elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1 and self.help_ok.collidepoint(getattr(event, "pos", pygame.mouse.get_pos())):
                    self.state = self.STATE_HOME
            elif self.state == self.STATE_PLAY:
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_LEFT:
                        self.selected_path = max(0, self.selected_path - 1)
                    elif event.key == pygame.K_RIGHT:
                        self.selected_path = min(2, self.selected_path + 1)
                    elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
                        correct = self.scoring.on_answer(self.selected_path == self.round_data["target"])
                        if correct:
                            self.play_correct_sound()
                        else:
                            self.play_wrong_sound()
                        self._set_feedback("path_fusion.feedback.hit" if correct else "path_fusion.feedback.miss", (86, 174, 112) if correct else (214, 96, 96))
                        self._new_round()
                    elif event.key == pygame.K_ESCAPE:
                        self.manager.set_scene("menu")
                elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    pos = getattr(event, "pos", pygame.mouse.get_pos())
                    if self.btn_home.collidepoint(pos):
                        self.manager.set_scene("menu")
                    else:
                        for idx, rect in enumerate(self.option_rects):
                            if rect.collidepoint(pos):
                                self.selected_path = idx
                                correct = self.scoring.on_answer(idx == self.round_data["target"])
                                if correct:
                                    self.play_correct_sound()
                                else:
                                    self.play_wrong_sound()
                                self._set_feedback("path_fusion.feedback.hit" if correct else "path_fusion.feedback.miss", (86, 174, 112) if correct else (214, 96, 96))
                                self._new_round()
                                break
            else:
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    pos = getattr(event, "pos", pygame.mouse.get_pos())
                    if self.btn_continue.collidepoint(pos):
                        self.state = self.STATE_HOME
                    elif self.btn_exit.collidepoint(pos):
                        self.manager.set_scene("menu")

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
