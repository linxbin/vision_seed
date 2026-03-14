import math
import time
from datetime import datetime

import pygame

from core.asset_loader import load_image_if_exists, project_path
from core.base_scene import BaseScene
from ..services import PrecisionAimBoardService, PrecisionAimScoringService, PrecisionAimSessionService


class PrecisionAimScene(BaseScene):
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
        self.background_switched_at = time.time()
        self.background_phase = 0.0
        self.board_service = PrecisionAimBoardService()
        self.scoring = PrecisionAimScoringService()
        self.session = PrecisionAimSessionService(self._session_seconds())
        self.round_data = {}
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

    def reset(self):
        self.state = self.STATE_HOME
        self.feedback_text = ""
        self.final_stats = {}
        self.background_mode = "checker"
        self.background_switched_at = time.time()
        self.background_phase = 0.0
        self.scoring.reset()
        self.session.session_seconds = self._session_seconds()
        self.session.reset()

    def _session_seconds(self):
        try:
            minutes = int(self.manager.settings.get("session_duration_minutes", 5))
        except (TypeError, ValueError):
            minutes = 5
        return max(60, minutes * 60)

    def _stage_index(self):
        progress = min(1.0, self.session.session_elapsed / max(1.0, self.session.session_seconds)) if self.session.session_seconds else 0.0
        if progress < 0.34:
            return 0
        if progress < 0.67:
            return 1
        return 2

    def _load_ui_icon(self, icon_name, light=False, size=(18, 18)):
        suffix = "light" if light else "dark"
        return load_image_if_exists(project_path("assets", "ui", f"{icon_name}_{suffix}.png"), size)

    def _draw_button(self, screen, rect, text, color, text_color=(255, 255, 255), icon_name=None):
        hovered = rect.collidepoint(pygame.mouse.get_pos())
        fill = tuple(min(255, c + 18) for c in color) if hovered else color
        border = (255, 255, 255) if hovered else (202, 223, 246)
        pygame.draw.rect(screen, fill, rect, border_radius=10)
        pygame.draw.rect(screen, border, rect, 2, border_radius=10)
        label = self.option_font.render(text, True, text_color)
        icon = self._load_ui_icon(icon_name, light=sum(text_color) > 500) if icon_name else None
        gap = 8 if icon is not None else 0
        width = label.get_width() + (icon.get_width() + gap if icon is not None else 0)
        start_x = rect.centerx - width // 2
        if icon is not None:
            screen.blit(icon, (start_x, rect.centery - icon.get_height() // 2))
            start_x += icon.get_width() + gap
        screen.blit(label, (start_x, rect.centery - label.get_height() // 2))

    def _set_feedback(self, key, color):
        self.feedback_text = self.manager.t(key)
        self.feedback_color = color
        self.feedback_until = time.time() + 1.0

    def _play_sound(self, method_name):
        sound_manager = getattr(self.manager, "sound_manager", None)
        method = getattr(sound_manager, method_name, None) if sound_manager else None
        if method:
            method()

    def _new_round(self):
        self.round_data = self.board_service.create_round(self.play_area, self._stage_index(), 4)
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
            "avg_deviation": self.scoring.average_deviation(),
            "avg_aim_time": self.scoring.average_aim_time(),
            "smallest_target_hit": self.scoring.smallest_target_hit,
            "best_center_streak": self.scoring.best_center_streak,
        }
        self._play_sound("play_completed")
        self._save_result()

    def _save_result(self):
        data_manager = getattr(self.manager, "data_manager", None)
        if not data_manager:
            return
        total = self.scoring.success_count + self.scoring.failure_count
        data_manager.save_training_session(
            {
                "timestamp": datetime.now().isoformat(),
                "game_id": "amblyopia.precision_aim",
                "difficulty_level": 4,
                "total_questions": total,
                "correct_count": self.scoring.success_count,
                "wrong_count": self.scoring.failure_count,
                "duration_seconds": float(self.final_stats.get("duration", 0)),
                "accuracy_rate": self.final_stats.get("accuracy", 0.0),
                "training_metrics": {
                    "hit_accuracy": self.final_stats.get("accuracy", 0.0),
                    "avg_aim_time": self.final_stats.get("avg_aim_time", 0.0),
                    "average_click_deviation_px": self.final_stats.get("avg_deviation", 0.0),
                    "smallest_target_hit": self.final_stats.get("smallest_target_hit", 0),
                    "best_center_streak": self.final_stats.get("best_center_streak", 0),
                },
            }
        )

    def _go_category(self):
        self.manager.set_scene("category")

    def _go_menu(self):
        self.manager.set_scene("menu")

    def _draw_background(self, screen):
        top = (236, 244, 255)
        bottom = (221, 235, 250)
        for y in range(self.height):
            t = y / max(1, self.height - 1)
            color = (
                int(top[0] * (1 - t) + bottom[0] * t),
                int(top[1] * (1 - t) + bottom[1] * t),
                int(top[2] * (1 - t) + bottom[2] * t),
            )
            pygame.draw.line(screen, color, (0, y), (self.width, y))

    def _draw_stimulus_background(self, screen):
        area = self.play_area.inflate(40, 30)
        clip_rect = area.clip(pygame.Rect(0, 0, self.width, self.height))
        panel = pygame.Surface(clip_rect.size, pygame.SRCALPHA)
        panel.fill((255, 255, 255, 90))
        screen.blit(panel, clip_rect.topleft)
        offset = int(math.sin(self.background_phase) * 6)
        if self.background_mode == "checker":
            cell = 26
            for row, y in enumerate(range(clip_rect.top, clip_rect.bottom, cell)):
                for col, x in enumerate(range(clip_rect.left, clip_rect.right, cell)):
                    shade = 236 if (row + col) % 2 == 0 else 24
                    wobble = ((row % 2) * 2 - 1) * offset
                    rect = pygame.Rect(x + wobble, y, cell, cell)
                    pygame.draw.rect(screen, (shade, shade, shade), rect)
        else:
            stripe = 18
            for idx, x in enumerate(range(clip_rect.left - 24, clip_rect.right + 24, stripe)):
                shade = 242 if idx % 2 == 0 else 28
                drift = int(math.sin(self.background_phase + idx * 0.22) * 8)
                points = [
                    (x + drift, clip_rect.top),
                    (x + stripe + drift, clip_rect.top),
                    (x + stripe - drift, clip_rect.bottom),
                    (x - drift, clip_rect.bottom),
                ]
                pygame.draw.polygon(screen, (shade, shade, shade), points)
        pygame.draw.rect(screen, (220, 228, 238), clip_rect, 2, border_radius=18)

    def _handle_shot(self, x, y):
        dx = x - self.round_data["target_center"][0]
        dy = y - self.round_data["target_center"][1]
        distance = math.hypot(dx, dy)
        success, gained = self.scoring.on_shot(distance, self.round_data["current_radius"], self.session.round_elapsed, self.round_data["stage_index"])
        if success:
            key = {
                "center": "precision_aim.feedback.center",
                "good": "precision_aim.feedback.good",
                "edge": "precision_aim.feedback.edge",
            }.get(self.scoring.last_quality, "precision_aim.feedback.good")
            color = {
                "center": (82, 152, 222),
                "good": (86, 174, 112),
                "edge": (214, 148, 88),
            }.get(self.scoring.last_quality, (86, 174, 112))
            self._set_feedback(key, color)
            self.feedback_text = f"{self.feedback_text}  +{gained}"
            self._play_sound("play_correct")
        else:
            self._set_feedback("precision_aim.feedback.miss", (214, 96, 96))
            self._play_sound("play_wrong")
        self._new_round()

    def _update_target_motion(self, now):
        progress = min(1.0, self.session.round_elapsed / max(1.0, self.session.ROUND_SECONDS))
        shrink_progress = progress ** 0.78
        self.round_data["current_radius"] = max(10, int(self.round_data["base_radius"] * (1.0 - 0.62 * shrink_progress)))
        if self.round_data["stage_index"] == 2:
            drift_x = int(math.sin(now * 2.4 + self.round_data["challenge_shift"]) * 18)
            drift_y = int(math.cos(now * 1.9 + self.round_data["challenge_shift"]) * 12)
            anchor_x, anchor_y = self.round_data["anchor_center"]
            self.round_data["target_center"] = (anchor_x + drift_x, anchor_y + drift_y)
        else:
            self.round_data["target_center"] = self.round_data["anchor_center"]

    def _draw_help_step(self, screen, idx, y, text):
        pygame.draw.circle(screen, (255, 208, 124) if idx == 1 else (136, 198, 255) if idx == 2 else (162, 225, 162), (132, y + 18), 14)
        step = self.small_font.render(f"{idx}. {text}", True, (58, 84, 118))
        screen.blit(step, (160, y + 6))

    def _draw_home(self, screen):
        title = self.title_font.render(self.manager.t("precision_aim.title"), True, (38, 66, 108))
        screen.blit(title, (self.width // 2 - title.get_width() // 2, 86))
        self._draw_button(screen, self.btn_start, self.manager.t("precision_aim.home.start"), (206, 108, 108), icon_name="check")
        self._draw_button(screen, self.btn_help, self.manager.t("precision_aim.home.help"), (126, 142, 174), icon_name="question")
        self._draw_button(screen, self.btn_back, self.manager.t("common.back"), (88, 116, 168), icon_name="back_arrow")

    def _draw_help(self, screen):
        title = self.title_font.render(self.manager.t("precision_aim.help.title"), True, (42, 70, 110))
        screen.blit(title, (self.width // 2 - title.get_width() // 2, 76))
        self._draw_help_step(screen, 1, 190, self.manager.t("precision_aim.help.step1"))
        self._draw_help_step(screen, 2, 280, self.manager.t("precision_aim.help.step2"))
        self._draw_help_step(screen, 3, 370, self.manager.t("precision_aim.help.step3"))
        self._draw_button(screen, self.help_ok, self.manager.t("precision_aim.help.ok"), (242, 214, 126), text_color=(104, 84, 42), icon_name="check")

    def _draw_target(self, screen):
        cx, cy = self.round_data["target_center"]
        rings = [self.round_data["current_radius"], int(self.round_data["current_radius"] * 0.68), int(self.round_data["current_radius"] * 0.35)]
        colors = [(238, 116, 116), (250, 244, 208), (122, 188, 255)]
        for radius, color in zip(rings, colors):
            pygame.draw.circle(screen, color, (int(cx), int(cy)), max(4, radius))
        pygame.draw.circle(screen, (255, 255, 255), (int(cx), int(cy)), max(2, rings[-1] // 3))
        aim_x, aim_y = int(self.round_data["aim_center"][0]), int(self.round_data["aim_center"][1])
        pygame.draw.circle(screen, (255, 255, 255), (aim_x, aim_y), 14, 2)
        pygame.draw.line(screen, (72, 86, 122), (aim_x - 12, aim_y), (aim_x + 12, aim_y), 2)
        pygame.draw.line(screen, (72, 86, 122), (aim_x, aim_y - 12), (aim_x, aim_y + 12), 2)

    def _draw_play(self, screen):
        hud_primary = (55, 82, 122)
        hud_secondary = (86, 104, 130)
        hud_alert = (222, 74, 74)
        screen.blit(self.body_font.render(self.manager.t("precision_aim.mode.naked"), True, hud_primary), (24, 18))
        remaining = max(0, int(self.session.session_seconds - self.session.session_elapsed))
        timer = self.body_font.render(self.manager.t("precision_aim.time", sec=f"{remaining // 60:02d}:{remaining % 60:02d}"), True, hud_alert if remaining <= 30 else hud_primary)
        score = self.body_font.render(self.manager.t("precision_aim.score", score=self.scoring.score), True, hud_primary)
        screen.blit(timer, (self.width // 2 - timer.get_width() // 2, 14))
        screen.blit(score, (self.width // 2 - score.get_width() // 2, 44))
        stage = self.small_font.render(self.manager.t(self.board_service.stage_label_key(self.round_data["stage_index"])), True, hud_secondary)
        goal = self.small_font.render(self.manager.t(self.board_service.goal_label_key(self.round_data["stage_index"])), True, hud_secondary)
        guide = self.small_font.render(self.manager.t("precision_aim.play.guide"), True, hud_secondary)
        round_left = max(0, int(self.session.ROUND_SECONDS - self.session.round_elapsed))
        countdown = self.small_font.render(self.manager.t("precision_aim.round_time", sec=round_left), True, hud_alert if round_left <= 3 else hud_secondary)
        screen.blit(stage, (self.play_area.x, 98))
        screen.blit(goal, (self.play_area.right - goal.get_width(), 98))
        screen.blit(guide, (self.play_area.centerx - guide.get_width() // 2, 122))
        screen.blit(countdown, (self.play_area.centerx - countdown.get_width() // 2, self.play_area.bottom + 8))
        self._draw_stimulus_background(screen)
        self._draw_target(screen)
        if self.scoring.center_streak >= 2:
            streak = self.small_font.render(f"STREAK x{self.scoring.center_streak}", True, (72, 132, 208))
            screen.blit(streak, (self.play_area.right - streak.get_width() - 12, self.play_area.y + 12))
        if self.feedback_text and time.time() <= self.feedback_until:
            fb = self.body_font.render(self.feedback_text, True, self.feedback_color)
            screen.blit(fb, (self.width // 2 - fb.get_width() // 2, self.play_area.bottom + 34))
        self._draw_button(screen, self.btn_home, self.manager.t("common.back"), (86, 116, 170), icon_name="back_arrow")

    def _draw_result(self, screen):
        title = self.title_font.render(self.manager.t("precision_aim.result.title"), True, (42, 70, 110))
        screen.blit(title, (self.width // 2 - title.get_width() // 2, 100))
        lines = [
            self.manager.t("precision_aim.result.duration", sec=self.final_stats.get("duration", 0)),
            self.manager.t("precision_aim.result.success", n=self.final_stats.get("success", 0)),
            self.manager.t("precision_aim.result.wrong", n=self.final_stats.get("wrong", 0)),
            self.manager.t("precision_aim.result.accuracy", value=self.final_stats.get("accuracy", 0.0)),
            self.manager.t("precision_aim.result.score", n=self.final_stats.get("score", 0)),
            self.manager.t("precision_aim.result.deviation", value=self.final_stats.get("avg_deviation", 0.0)),
            self.manager.t("precision_aim.result.aim_time", sec=self.final_stats.get("avg_aim_time", 0.0)),
            self.manager.t("precision_aim.result.smallest", n=self.final_stats.get("smallest_target_hit", 0)),
            self.manager.t("precision_aim.result.streak", n=self.final_stats.get("best_center_streak", 0)),
        ]
        for idx, text in enumerate(lines):
            line = self.body_font.render(text, True, (58, 84, 118))
            screen.blit(line, (self.width // 2 - line.get_width() // 2, 176 + idx * 30))
        self._draw_button(screen, self.btn_continue, self.manager.t("precision_aim.result.continue"), (84, 148, 108), icon_name="check")
        self._draw_button(screen, self.btn_exit, self.manager.t("precision_aim.result.exit"), (120, 134, 168), icon_name="cross")

    def handle_events(self, events):
        for event in events:
            if self.state == self.STATE_HOME:
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        self._go_category()
                    elif event.key == pygame.K_1:
                        self._start_game()
                    elif event.key == pygame.K_2:
                        self.state = self.STATE_HELP
                elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    pos = getattr(event, "pos", pygame.mouse.get_pos())
                    if self.btn_back.collidepoint(pos):
                        self._go_category()
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
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        self._go_category()
                    elif event.key == pygame.K_LEFT:
                        self.round_data["aim_center"][0] -= 22
                    elif event.key == pygame.K_RIGHT:
                        self.round_data["aim_center"][0] += 22
                    elif event.key == pygame.K_UP:
                        self.round_data["aim_center"][1] -= 22
                    elif event.key == pygame.K_DOWN:
                        self.round_data["aim_center"][1] += 22
                    elif event.key in (pygame.K_SPACE, pygame.K_RETURN):
                        self._handle_shot(self.round_data["aim_center"][0], self.round_data["aim_center"][1])
                elif event.type == pygame.MOUSEMOTION:
                    self.round_data["aim_center"][0] = event.pos[0]
                    self.round_data["aim_center"][1] = event.pos[1]
                elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    pos = getattr(event, "pos", pygame.mouse.get_pos())
                    if self.btn_home.collidepoint(pos):
                        self._go_category()
                    else:
                        self._handle_shot(pos[0], pos[1])
                self.round_data["aim_center"][0] = max(self.play_area.left + 20, min(self.play_area.right - 20, self.round_data["aim_center"][0]))
                self.round_data["aim_center"][1] = max(self.play_area.top + 20, min(self.play_area.bottom - 20, self.round_data["aim_center"][1]))
            else:
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_RETURN:
                        self.state = self.STATE_HOME
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
            self.background_phase += 0.045
            if now - self.background_switched_at >= 6.0:
                self.background_mode = "stripe" if self.background_mode == "checker" else "checker"
                self.background_switched_at = now
            self._update_target_motion(now)
            if self.session.is_session_complete():
                self._finish_game()
                return
            if self.session.is_round_timed_out():
                self.scoring.failure_count += 1
                self.scoring.center_streak = 0
                self._set_feedback("precision_aim.feedback.timeout", (214, 96, 96))
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
