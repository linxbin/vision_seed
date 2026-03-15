import time
from datetime import datetime

import pygame

from core.base_scene import BaseScene
from ..services import WhackAMoleBoardService, WhackAMoleScoringService, WhackAMoleSessionService


class WhackAMoleScene(BaseScene):
    STATE_HOME = "home"
    STATE_HELP = "help"
    STATE_PLAY = "play"
    STATE_RESULT = "result"

    def __init__(self, manager):
        super().__init__(manager)
        self.width = 900
        self.height = 700
        self.state = self.STATE_HOME
        self.feedback_text = ""
        self.feedback_color = (255, 255, 255)
        self.feedback_until = 0.0
        self.final_stats = {}
        self.background_mode = "checker"
        self.background_phase = 0.0
        self.background_switched_at = time.time()
        self.previous_index = None
        self.board_service = WhackAMoleBoardService()
        self.scoring = WhackAMoleScoringService()
        self.session = WhackAMoleSessionService(self._session_seconds())
        self.round_data = {}
        self._refresh_fonts()
        self._build_ui()

    def _refresh_fonts(self):
        self.title_font = self.create_font(54)
        self.option_font = self.create_font(28)
        self.body_font = self.create_font(22)
        self.small_font = self.create_font(18)

    def _build_ui(self):
        card_w = min(560, self.width - 120)
        start_x = self.width // 2 - card_w // 2
        self.btn_start = pygame.Rect(start_x, 220, card_w, 58)
        self.btn_help = pygame.Rect(start_x, 296, card_w, 58)
        self.btn_back = pygame.Rect(self.width - 110, 18, 88, 36)
        self.btn_home = pygame.Rect(self.width - 110, 18, 88, 36)
        self.btn_continue = pygame.Rect(self.width // 2 - 210, self.height - 100, 180, 48)
        self.btn_exit = pygame.Rect(self.width // 2 + 30, self.height - 100, 180, 48)
        self.help_ok = pygame.Rect(self.width // 2 - 90, self.height - 90, 180, 54)
        self.play_area = pygame.Rect(70, 136, self.width - 140, self.height - 238)

    def on_resize(self, width, height):
        self.width = width
        self.height = height
        self._build_ui()
        if self.state == self.STATE_PLAY:
            self._new_round()

    def _session_seconds(self):
        try:
            minutes = int(self.manager.settings.get("session_duration_minutes", 5))
        except (TypeError, ValueError):
            minutes = 5
        return max(60, minutes * 60)

    def _stage_index(self):
        progress = min(1.0, self.session.session_elapsed / max(1.0, self.session.session_seconds)) if self.session.session_seconds else 0.0
        return 0 if progress < 0.34 else 1 if progress < 0.67 else 2

    def _draw_button(self, screen, rect, text, color, text_color=(255, 255, 255)):
        hovered = rect.collidepoint(pygame.mouse.get_pos())
        fill = tuple(min(255, c + 18) for c in color) if hovered else color
        pygame.draw.rect(screen, fill, rect, border_radius=10)
        pygame.draw.rect(screen, (255, 255, 255), rect, 2, border_radius=10)
        label = self.option_font.render(text, True, text_color)
        screen.blit(label, (rect.centerx - label.get_width() // 2, rect.centery - label.get_height() // 2))

    def _draw_background(self, screen):
        top = (236, 244, 255)
        bottom = (221, 235, 250)
        for y in range(self.height):
            t = y / max(1, self.height - 1)
            color = (int(top[0] * (1 - t) + bottom[0] * t), int(top[1] * (1 - t) + bottom[1] * t), int(top[2] * (1 - t) + bottom[2] * t))
            pygame.draw.line(screen, color, (0, y), (self.width, y))

    def _draw_stimulus_background(self, screen):
        clip_rect = self.play_area.inflate(40, 30)
        pattern_surface = pygame.Surface(clip_rect.size)
        offset = int(self.background_phase * 10) % 26
        if self.background_mode == "checker":
            cell = 26
            for row, y in enumerate(range(0, clip_rect.height, cell)):
                for col, x in enumerate(range(0, clip_rect.width, cell)):
                    shade = 236 if (row + col) % 2 == 0 else 24
                    pygame.draw.rect(pattern_surface, (shade, shade, shade), pygame.Rect(x, y, cell, cell))
        else:
            stripe = 18
            for idx, x in enumerate(range(-stripe + offset, clip_rect.width + stripe, stripe)):
                shade = 242 if idx % 2 == 0 else 28
                pygame.draw.rect(pattern_surface, (shade, shade, shade), pygame.Rect(x, 0, stripe, clip_rect.height))
        screen.blit(pattern_surface, clip_rect.topleft)
        pygame.draw.rect(screen, (220, 228, 238), clip_rect, 2, border_radius=18)

    def _new_round(self):
        self.round_data = self.board_service.create_round(self.play_area, self._stage_index(), self.previous_index)
        self.previous_index = self.round_data["active_index"]
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
        self.final_stats = {
            "duration": int(self.session.session_elapsed),
            "success": self.scoring.success_count,
            "wrong": self.scoring.failure_count,
            "accuracy": self.scoring.accuracy(),
            "score": self.scoring.score,
            "avg_aim_time": self.scoring.average_aim_time(),
            "center_hit_rate": self.scoring.center_hit_rate(),
            "best_streak": self.scoring.best_streak,
        }
        if getattr(self.manager, "data_manager", None):
            self.manager.data_manager.save_training_session({
                "timestamp": datetime.now().isoformat(),
                "game_id": "amblyopia.whack_a_mole",
                "difficulty_level": 3,
                "total_questions": self.scoring.success_count + self.scoring.failure_count,
                "correct_count": self.scoring.success_count,
                "wrong_count": self.scoring.failure_count,
                "duration_seconds": float(self.final_stats["duration"]),
                "accuracy_rate": self.final_stats["accuracy"],
                "training_metrics": {
                    "hit_accuracy": self.final_stats["accuracy"],
                    "center_hit_rate": self.final_stats["center_hit_rate"],
                    "avg_aim_time": self.final_stats["avg_aim_time"],
                    "best_streak": self.final_stats["best_streak"],
                },
            })
        self.play_completed_sound()

    def _set_feedback(self, key, color):
        self.feedback_text = self.manager.t(key)
        self.feedback_color = color
        self.feedback_until = time.time() + 0.9

    def _handle_hit(self, pos):
        distance = self.board_service.hit_distance(pos, self.round_data["target_center"])
        result, gained = self.scoring.on_hit(distance, self.round_data["radius"], self.session.round_elapsed)
        if result == "center":
            self.play_correct_sound()
            self._set_feedback("whack_a_mole.feedback.center", (82, 152, 222))
        elif result == "good":
            self.play_correct_sound()
            self._set_feedback("whack_a_mole.feedback.good", (86, 174, 112))
        else:
            self.play_wrong_sound()
            self._set_feedback("whack_a_mole.feedback.miss", (214, 96, 96))
        if result != "miss":
            self.feedback_text = f"{self.feedback_text}  +{gained}"
        self._new_round()

    def _draw_home(self, screen):
        title = self.title_font.render(self.manager.t("whack_a_mole.title"), True, (38, 66, 108))
        screen.blit(title, (self.width // 2 - title.get_width() // 2, 86))
        self._draw_button(screen, self.btn_start, self.manager.t("whack_a_mole.home.start"), (206, 108, 108))
        self._draw_button(screen, self.btn_help, self.manager.t("whack_a_mole.home.help"), (126, 142, 174))
        self._draw_button(screen, self.btn_back, self.manager.t("common.back"), (88, 116, 168))

    def _draw_help(self, screen):
        title = self.title_font.render(self.manager.t("whack_a_mole.help.title"), True, (42, 70, 110))
        screen.blit(title, (self.width // 2 - title.get_width() // 2, 76))
        for idx, key in enumerate(("whack_a_mole.help.step1", "whack_a_mole.help.step2", "whack_a_mole.help.step3")):
            step = self.body_font.render(f"{idx + 1}. {self.manager.t(key)}", True, (58, 84, 118))
            screen.blit(step, (118, 196 + idx * 90))
        self._draw_button(screen, self.help_ok, self.manager.t("whack_a_mole.help.ok"), (242, 214, 126), text_color=(104, 84, 42))

    def _draw_play(self, screen):
        self._draw_stimulus_background(screen)
        remaining = max(0, int(self.session.session_seconds - self.session.session_elapsed))
        round_left = max(0, int(self.session.ROUND_SECONDS - self.session.round_elapsed))
        screen.blit(self.body_font.render(self.manager.t("whack_a_mole.mode.naked"), True, (55, 82, 122)), (24, 18))
        timer = self.body_font.render(self.manager.t("whack_a_mole.time", sec=f"{remaining // 60:02d}:{remaining % 60:02d}"), True, (222, 74, 74) if remaining <= 30 else (55, 82, 122))
        score = self.body_font.render(self.manager.t("whack_a_mole.score", score=self.scoring.score), True, (55, 82, 122))
        stage = self.small_font.render(self.manager.t(self.board_service.stage_label_key(self.round_data["stage_index"])), True, (86, 104, 130))
        goal = self.small_font.render(self.manager.t(self.board_service.goal_label_key(self.round_data["stage_index"])), True, (86, 104, 130))
        guide = self.small_font.render(self.manager.t("whack_a_mole.play.guide"), True, (86, 104, 130))
        round_time = self.small_font.render(self.manager.t("whack_a_mole.round_time", sec=round_left), True, (222, 74, 74) if round_left <= 2 else (86, 104, 130))
        screen.blit(timer, (self.width // 2 - timer.get_width() // 2, 14))
        screen.blit(score, (self.width // 2 - score.get_width() // 2, 44))
        screen.blit(stage, (self.play_area.x, 98))
        screen.blit(goal, (self.play_area.right - goal.get_width(), 98))
        screen.blit(guide, (self.play_area.centerx - guide.get_width() // 2, self.play_area.y - 44))
        screen.blit(round_time, (self.play_area.centerx - round_time.get_width() // 2, self.play_area.bottom + 20))
        for idx, center in enumerate(self.round_data["holes"]):
            cx, cy = int(center[0]), int(center[1])
            hole = pygame.Rect(0, 0, 110, 42)
            hole.center = (cx, cy + 28)
            pygame.draw.ellipse(screen, (44, 44, 44), hole)
            if idx == self.round_data["active_index"]:
                radius = self.round_data["radius"]
                pygame.draw.circle(screen, (232, 198, 152), (cx, cy - 8), radius)
                pygame.draw.circle(screen, (46, 46, 46), (cx - radius // 3, cy - 12), 5)
                pygame.draw.circle(screen, (46, 46, 46), (cx + radius // 3, cy - 12), 5)
                pygame.draw.ellipse(screen, (124, 70, 70), pygame.Rect(cx - radius // 3, cy + 2, radius // 1.5, radius // 3))
        if self.feedback_text and time.time() <= self.feedback_until:
            fb = self.body_font.render(self.feedback_text, True, self.feedback_color)
            screen.blit(fb, (self.width // 2 - fb.get_width() // 2, self.play_area.bottom + 54))
        self._draw_button(screen, self.btn_home, self.manager.t("common.back"), (86, 116, 170))

    def _draw_result(self, screen):
        title = self.title_font.render(self.manager.t("whack_a_mole.result.title"), True, (42, 70, 110))
        screen.blit(title, (self.width // 2 - title.get_width() // 2, 100))
        lines = [
            self.manager.t("whack_a_mole.result.duration", sec=self.final_stats.get("duration", 0)),
            self.manager.t("whack_a_mole.result.success", n=self.final_stats.get("success", 0)),
            self.manager.t("whack_a_mole.result.wrong", n=self.final_stats.get("wrong", 0)),
            self.manager.t("whack_a_mole.result.accuracy", value=self.final_stats.get("accuracy", 0.0)),
            self.manager.t("whack_a_mole.result.score", n=self.final_stats.get("score", 0)),
            self.manager.t("whack_a_mole.result.aim_time", sec=self.final_stats.get("avg_aim_time", 0.0)),
            self.manager.t("whack_a_mole.result.center_rate", value=self.final_stats.get("center_hit_rate", 0.0)),
            self.manager.t("whack_a_mole.result.streak", n=self.final_stats.get("best_streak", 0)),
        ]
        for idx, text in enumerate(lines):
            line = self.body_font.render(text, True, (58, 84, 118))
            screen.blit(line, (self.width // 2 - line.get_width() // 2, 176 + idx * 30))
        self._draw_button(screen, self.btn_continue, self.manager.t("whack_a_mole.result.continue"), (84, 148, 108))
        self._draw_button(screen, self.btn_exit, self.manager.t("whack_a_mole.result.exit"), (120, 134, 168))

    def handle_events(self, events):
        for event in events:
            if self.state == self.STATE_HOME:
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_1:
                        self._start_game()
                    elif event.key == pygame.K_2:
                        self.state = self.STATE_HELP
                    elif event.key == pygame.K_ESCAPE:
                        self.manager.set_scene("category")
                elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    pos = getattr(event, "pos", pygame.mouse.get_pos())
                    if self.btn_back.collidepoint(pos):
                        self.manager.set_scene("category")
                    elif self.btn_start.collidepoint(pos):
                        self._start_game()
                    elif self.btn_help.collidepoint(pos):
                        self.state = self.STATE_HELP
            elif self.state == self.STATE_HELP:
                if event.type == pygame.KEYDOWN and event.key in (pygame.K_ESCAPE, pygame.K_RETURN):
                    self.state = self.STATE_HOME
                elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1 and self.help_ok.collidepoint(getattr(event, "pos", pygame.mouse.get_pos())):
                    self.state = self.STATE_HOME
            elif self.state == self.STATE_PLAY:
                if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                    self.manager.set_scene("category")
                elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    pos = getattr(event, "pos", pygame.mouse.get_pos())
                    if self.btn_home.collidepoint(pos):
                        self.manager.set_scene("category")
                    else:
                        self._handle_hit(pos)
            else:
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_RETURN:
                        self.state = self.STATE_HOME
                    elif event.key == pygame.K_ESCAPE:
                        self.manager.set_scene("menu")
                elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    pos = getattr(event, "pos", pygame.mouse.get_pos())
                    if self.btn_continue.collidepoint(pos):
                        self.state = self.STATE_HOME
                    elif self.btn_exit.collidepoint(pos):
                        self.manager.set_scene("menu")

    def update(self):
        now = time.time()
        if self.state == self.STATE_PLAY:
            self.session.tick(now)
            self.background_phase += 0.05
            if now - self.background_switched_at >= 6.0:
                self.background_mode = "stripe" if self.background_mode == "checker" else "checker"
                self.background_switched_at = now
            if self.session.is_session_complete():
                self._finish_game()
            elif self.session.is_round_timed_out():
                self.scoring.on_timeout()
                self.play_wrong_sound()
                self._set_feedback("whack_a_mole.feedback.timeout", (214, 96, 96))
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
