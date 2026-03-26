import math
import time
from datetime import datetime

import pygame

from core.base_scene import BaseScene
from ..services import FruitSliceBoardService, FruitSliceScoringService, FruitSliceSessionService


class FruitSliceScene(BaseScene):
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
        self.board_service = FruitSliceBoardService()
        self.scoring = FruitSliceScoringService()
        self.session = FruitSliceSessionService(self._session_seconds())
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

    def _set_feedback(self, key, color):
        self.feedback_text = self.manager.t(key)
        self.feedback_color = color
        self.feedback_until = time.time() + 0.9

    def _new_round(self):
        self.round_data = self.board_service.create_round(self.play_area)
        self.session.restart_round()

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
                "game_id": "amblyopia.fruit_slice",
                "difficulty_level": 3,
                "total_questions": self.scoring.success_count + self.scoring.failure_count,
                "correct_count": self.scoring.success_count,
                "wrong_count": self.scoring.failure_count,
                "duration_seconds": float(self.final_stats.get("duration", 0)),
                "accuracy_rate": self.final_stats.get("accuracy", 0.0),
                "training_metrics": {
                    "slice_accuracy": self.final_stats.get("accuracy", 0.0),
                    "bonus_hits": 0,
                    "best_combo": self.final_stats.get("best_combo", 0),
                },
            })

    def _finish_game(self):
        self.final_stats = {
            "duration": int(self.session.session_elapsed),
            "success": self.scoring.success_count,
            "wrong": self.scoring.failure_count,
            "accuracy": self.scoring.accuracy(),
            "score": self.scoring.score,
            "best_combo": self.scoring.best_combo,
        }
        self.state = self.STATE_RESULT
        self.play_completed_sound()
        self._save_result()

    def _draw_home(self, screen):
        title = self.title_font.render(self.manager.t("fruit_slice.title"), True, (38, 66, 108))
        screen.blit(title, (self.width // 2 - title.get_width() // 2, 86))
        self._draw_button(screen, self.btn_start, self.manager.t("fruit_slice.home.start"), (206, 108, 108))
        self._draw_button(screen, self.btn_help, self.manager.t("fruit_slice.home.help"), (126, 142, 174))
        self._draw_button(screen, self.btn_back, self.manager.t("common.back"), (88, 116, 168))

    def _draw_help(self, screen):
        title = self.title_font.render(self.manager.t("fruit_slice.help.title"), True, (42, 70, 110))
        screen.blit(title, (self.width // 2 - title.get_width() // 2, 76))
        for idx, key in enumerate(("fruit_slice.help.step1", "fruit_slice.help.step2", "fruit_slice.help.step3")):
            line = self.body_font.render(f"{idx + 1}. {self.manager.t(key)}", True, (58, 84, 118))
            screen.blit(line, (110, 196 + idx * 90))
        self._draw_button(screen, self.help_ok, self.manager.t("fruit_slice.help.ok"), (242, 214, 126), text_color=(104, 84, 42))

    def _draw_play(self, screen):
        self._draw_stimulus_background(screen)
        remaining = max(0, int(self.session.session_seconds - self.session.session_elapsed))
        timer = self.body_font.render(self.manager.t("fruit_slice.time", sec=f"{remaining // 60:02d}:{remaining % 60:02d}"), True, (222, 74, 74) if remaining <= 30 else (55, 82, 122))
        score = self.body_font.render(self.manager.t("fruit_slice.score", score=self.scoring.score), True, (55, 82, 122))
        guide = self.small_font.render(self.manager.t("fruit_slice.play.guide"), True, (86, 104, 130))
        screen.blit(self.body_font.render(self.manager.t("fruit_slice.mode.naked"), True, (55, 82, 122)), (24, 18))
        screen.blit(timer, (self.width // 2 - timer.get_width() // 2, 14))
        screen.blit(score, (self.width // 2 - score.get_width() // 2, 44))
        screen.blit(guide, (self.play_area.centerx - guide.get_width() // 2, self.play_area.y - 44))
        for item in self.round_data.get("items", ()):
            cx, cy = item["center"]
            if item["is_bomb"]:
                pygame.draw.circle(screen, (48, 48, 48), (cx, cy), item["radius"])
                pygame.draw.line(screen, (250, 210, 120), (cx, cy - item["radius"]), (cx + 10, cy - item["radius"] - 16), 4)
            else:
                pygame.draw.circle(screen, item["color"], (cx, cy), item["radius"])
                pygame.draw.arc(screen, (255, 255, 255), pygame.Rect(cx - item["radius"] // 2, cy - 8, item["radius"], item["radius"] // 2), math.pi, math.pi * 2, 3)
        if self.feedback_text and time.time() <= self.feedback_until:
            fb = self.body_font.render(self.feedback_text, True, self.feedback_color)
            screen.blit(fb, (self.width // 2 - fb.get_width() // 2, self.play_area.bottom + 20))
        self._draw_button(screen, self.btn_home, self.manager.t("common.back"), (86, 116, 170))

    def _draw_result(self, screen):
        title = self.title_font.render(self.manager.t("fruit_slice.result.title"), True, (42, 70, 110))
        screen.blit(title, (self.width // 2 - title.get_width() // 2, 100))
        lines = [
            self.manager.t("fruit_slice.result.duration", sec=self.final_stats.get("duration", 0)),
            self.manager.t("fruit_slice.result.success", n=self.final_stats.get("success", 0)),
            self.manager.t("fruit_slice.result.wrong", n=self.final_stats.get("wrong", 0)),
            self.manager.t("fruit_slice.result.accuracy", value=self.final_stats.get("accuracy", 0.0)),
            self.manager.t("fruit_slice.result.score", n=self.final_stats.get("score", 0)),
            self.manager.t("fruit_slice.result.combo", n=self.final_stats.get("best_combo", 0)),
        ]
        for idx, text in enumerate(lines):
            line = self.body_font.render(text, True, (58, 84, 118))
            screen.blit(line, (self.width // 2 - line.get_width() // 2, 176 + idx * 34))
        self._draw_button(screen, self.btn_continue, self.manager.t("fruit_slice.result.continue"), (84, 148, 108))
        self._draw_button(screen, self.btn_exit, self.manager.t("fruit_slice.result.exit"), (120, 134, 168))

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
                        clicked_item = None
                        for item in self.round_data.get("items", ()):
                            distance = math.hypot(pos[0] - item["center"][0], pos[1] - item["center"][1])
                            if distance <= item["radius"]:
                                clicked_item = item
                                break
                        if clicked_item:
                            if clicked_item["is_bomb"]:
                                self.scoring.on_failure()
                                self.play_wrong_sound()
                                self._set_feedback("fruit_slice.feedback.bomb", (214, 96, 96))
                            else:
                                self.scoring.on_target()
                                self.play_correct_sound()
                                self._set_feedback("fruit_slice.feedback.hit", (86, 174, 112))
                            self._new_round()
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
            self.background_phase += 0.05 * self.frame_scale()
            if now - self.background_switched_at >= 6.0:
                self.background_mode = "stripe" if self.background_mode == "checker" else "checker"
                self.background_switched_at = now
            if self.session.is_complete():
                self._finish_game()
            elif self.session.is_round_complete():
                self.scoring.on_failure()
                self.play_wrong_sound()
                self._set_feedback("fruit_slice.feedback.miss", (214, 96, 96))
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
