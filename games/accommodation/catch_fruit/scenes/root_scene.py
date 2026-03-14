import time
from datetime import datetime

import pygame

from core.asset_loader import load_image_if_exists, project_path
from core.base_scene import BaseScene
from ..services import CatchFruitBoardService, CatchFruitScoringService, CatchFruitSessionService


class CatchFruitScene(BaseScene):
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
        self.board_service = CatchFruitBoardService()
        self.scoring = CatchFruitScoringService()
        self.session = CatchFruitSessionService(self._session_seconds())
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

    def reset(self):
        self.state = self.STATE_HOME
        self.feedback_text = ""
        self.final_stats = {}
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
        self.round_data = self.board_service.create_round(self.play_area, self._stage_index(), 3)
        self.session.restart_round(time.time())

    def _start_game(self):
        self.state = self.STATE_PLAY
        self.scoring.reset()
        self.session.session_seconds = self._session_seconds()
        self.session.start()
        self.feedback_text = ""
        self._new_round()

    def _clarity(self):
        span = max(1, self.play_area.height - 80)
        return min(1.0, max(0.0, (self.round_data["fruit_y"] - self.play_area.top) / span))

    def _current_size(self):
        return int(self.round_data["start_size"] - (self.round_data["start_size"] - self.round_data["end_size"]) * self._clarity())

    def _resolve_catch(self, success):
        if success:
            gained = self.scoring.on_catch(self._current_size(), self._clarity(), self.round_data["fruit_name"], self.round_data["stage_index"], self.board_service.fruit_points)
            if self.scoring.last_success_bonus:
                self._set_feedback("catch_fruit.feedback.bonus", (88, 162, 108))
            elif self.scoring.current_streak >= 3:
                self._set_feedback("catch_fruit.feedback.combo", (92, 156, 222))
            else:
                self._set_feedback("arcade.play.correct", (86, 174, 112))
            self.feedback_text = f"{self.feedback_text}  +{gained}"
            self._play_sound("play_correct")
        else:
            self.scoring.on_miss()
            self._set_feedback("catch_fruit.feedback.miss", (214, 96, 96))
            self._play_sound("play_wrong")
        self._new_round()

    def _finish_game(self):
        self.state = self.STATE_RESULT
        self.final_stats = {
            "duration": int(self.session.session_elapsed),
            "success": self.scoring.success_count,
            "wrong": self.scoring.failure_count,
            "accuracy": self.scoring.accuracy(),
            "score": self.scoring.score,
            "smallest_caught_size_px": self.scoring.smallest_caught,
            "clear_hits": self.scoring.clear_hits,
            "best_streak": self.scoring.best_streak,
            "bonus_hits": self.scoring.bonus_hits,
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
                "game_id": "accommodation.catch_fruit",
                "difficulty_level": 3,
                "total_questions": total,
                "correct_count": self.scoring.success_count,
                "wrong_count": self.scoring.failure_count,
                "duration_seconds": float(self.final_stats.get("duration", 0)),
                "accuracy_rate": self.final_stats.get("accuracy", 0.0),
                "training_metrics": {
                    "smallest_caught_size_px": self.final_stats.get("smallest_caught_size_px", 0),
                    "clear_window_hits": self.final_stats.get("clear_hits", 0),
                    "best_streak": self.final_stats.get("best_streak", 0),
                    "bonus_hits": self.final_stats.get("bonus_hits", 0),
                },
            }
        )

    def _go_category(self):
        self.manager.set_scene("category")

    def _go_menu(self):
        self.manager.set_scene("menu")

    def _draw_background(self, screen):
        top = (240, 248, 233)
        bottom = (222, 240, 218)
        for y in range(self.height):
            t = y / max(1, self.height - 1)
            color = (
                int(top[0] * (1 - t) + bottom[0] * t),
                int(top[1] * (1 - t) + bottom[1] * t),
                int(top[2] * (1 - t) + bottom[2] * t),
            )
            pygame.draw.line(screen, color, (0, y), (self.width, y))

    def _draw_help_step(self, screen, idx, y, text):
        pygame.draw.circle(screen, (255, 208, 124) if idx == 1 else (136, 198, 255) if idx == 2 else (162, 225, 162), (132, y + 18), 14)
        step = self.small_font.render(f"{idx}. {text}", True, (58, 84, 118))
        screen.blit(step, (160, y + 6))

    def _draw_home(self, screen):
        title = self.title_font.render(self.manager.t("catch_fruit.title"), True, (56, 108, 68))
        screen.blit(title, (self.width // 2 - title.get_width() // 2, 86))
        self._draw_button(screen, self.btn_start, self.manager.t("catch_fruit.home.start"), (96, 156, 104), icon_name="check")
        self._draw_button(screen, self.btn_help, self.manager.t("catch_fruit.home.help"), (126, 142, 174), icon_name="question")
        self._draw_button(screen, self.btn_back, self.manager.t("common.back"), (88, 116, 168), icon_name="back_arrow")

    def _draw_help(self, screen):
        title = self.title_font.render(self.manager.t("catch_fruit.help.title"), True, (42, 96, 58))
        screen.blit(title, (self.width // 2 - title.get_width() // 2, 76))
        self._draw_help_step(screen, 1, 190, self.manager.t("catch_fruit.help.step1"))
        self._draw_help_step(screen, 2, 280, self.manager.t("catch_fruit.help.step2"))
        self._draw_help_step(screen, 3, 370, self.manager.t("catch_fruit.help.step3"))
        self._draw_button(screen, self.help_ok, self.manager.t("catch_fruit.help.ok"), (242, 214, 126), text_color=(104, 84, 42), icon_name="check")

    def _draw_play(self, screen):
        hud_primary = (65, 110, 72)
        hud_secondary = (84, 110, 96)
        hud_alert = (222, 74, 74)
        screen.blit(self.body_font.render(self.manager.t("catch_fruit.mode.naked"), True, hud_primary), (24, 18))
        remaining = max(0, int(self.session.session_seconds - self.session.session_elapsed))
        timer = self.body_font.render(self.manager.t("catch_fruit.time", sec=f"{remaining // 60:02d}:{remaining % 60:02d}"), True, hud_alert if remaining <= 30 else hud_primary)
        score = self.body_font.render(self.manager.t("catch_fruit.score", score=self.scoring.score), True, hud_primary)
        screen.blit(timer, (self.width // 2 - timer.get_width() // 2, 14))
        screen.blit(score, (self.width // 2 - score.get_width() // 2, 44))
        stage = self.small_font.render(self.manager.t(self.board_service.stage_label_key(self.round_data["stage_index"])), True, hud_secondary)
        goal = self.small_font.render(self.manager.t(self.board_service.goal_label_key(self.round_data["stage_index"])), True, hud_secondary)
        guide = self.small_font.render(self.manager.t("catch_fruit.play.guide"), True, hud_secondary)
        screen.blit(stage, (self.play_area.x, 98))
        screen.blit(goal, (self.play_area.right - goal.get_width(), 98))
        screen.blit(guide, (self.play_area.centerx - guide.get_width() // 2, 122))
        basket = pygame.Rect(0, 0, 132, 28)
        basket.center = (int(self.round_data["basket_x"]), self.play_area.bottom - 26)
        basket_surface = load_image_if_exists(self.board_service.basket_asset, (148, 52))
        if basket_surface is not None:
            screen.blit(basket_surface, basket_surface.get_rect(center=basket.center))
        else:
            pygame.draw.rect(screen, (176, 118, 62), basket, border_radius=14)
        clarity = self._clarity()
        size = self._current_size()
        halo = pygame.Surface((size * 3, size * 3), pygame.SRCALPHA)
        pygame.draw.circle(halo, (255, 223, 142, int(150 * (1.0 - clarity))), (halo.get_width() // 2, halo.get_height() // 2), size)
        fruit_center = (int(self.round_data["fruit_x"]), int(self.round_data["fruit_y"]))
        screen.blit(halo, halo.get_rect(center=fruit_center))
        fruit_surface = load_image_if_exists(self.board_service.fruit_assets[self.round_data["fruit_name"]], (size, size))
        if fruit_surface is not None:
            screen.blit(fruit_surface, fruit_surface.get_rect(center=fruit_center))
        else:
            pygame.draw.circle(screen, (255, 98, 86), fruit_center, size // 2)
        if self.feedback_text and time.time() <= self.feedback_until:
            fb = self.body_font.render(self.feedback_text, True, self.feedback_color)
            screen.blit(fb, (self.width // 2 - fb.get_width() // 2, self.play_area.bottom + 20))
        self._draw_button(screen, self.btn_home, self.manager.t("common.back"), (88, 116, 168), icon_name="back_arrow")

    def _draw_result(self, screen):
        title = self.title_font.render(self.manager.t("catch_fruit.result.title"), True, (42, 96, 58))
        screen.blit(title, (self.width // 2 - title.get_width() // 2, 100))
        lines = [
            self.manager.t("catch_fruit.result.duration", sec=self.final_stats.get("duration", 0)),
            self.manager.t("catch_fruit.result.success", n=self.final_stats.get("success", 0)),
            self.manager.t("catch_fruit.result.wrong", n=self.final_stats.get("wrong", 0)),
            self.manager.t("catch_fruit.result.accuracy", value=self.final_stats.get("accuracy", 0.0)),
            self.manager.t("catch_fruit.result.score", n=self.final_stats.get("score", 0)),
            self.manager.t("catch_fruit.result.smallest", n=self.final_stats.get("smallest_caught_size_px", 0)),
            self.manager.t("catch_fruit.result.clear_hits", n=self.final_stats.get("clear_hits", 0)),
            self.manager.t("catch_fruit.result.streak", n=self.final_stats.get("best_streak", 0)),
            self.manager.t("catch_fruit.result.bonus", n=self.final_stats.get("bonus_hits", 0)),
        ]
        for idx, text in enumerate(lines):
            line = self.body_font.render(text, True, (58, 84, 118))
            screen.blit(line, (self.width // 2 - line.get_width() // 2, 176 + idx * 30))
        self._draw_button(screen, self.btn_continue, self.manager.t("catch_fruit.result.continue"), (84, 148, 108), icon_name="check")
        self._draw_button(screen, self.btn_exit, self.manager.t("catch_fruit.result.exit"), (120, 134, 168), icon_name="cross")

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
                        self.round_data["move_dir"] = -1
                    elif event.key == pygame.K_RIGHT:
                        self.round_data["move_dir"] = 1
                elif event.type == pygame.KEYUP:
                    if event.key == pygame.K_LEFT and self.round_data["move_dir"] < 0:
                        self.round_data["move_dir"] = 0
                    elif event.key == pygame.K_RIGHT and self.round_data["move_dir"] > 0:
                        self.round_data["move_dir"] = 0
                elif event.type == pygame.MOUSEMOTION:
                    self.round_data["basket_x"] = max(self.play_area.left + 60, min(self.play_area.right - 60, event.pos[0]))
                elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    pos = getattr(event, "pos", pygame.mouse.get_pos())
                    if self.btn_home.collidepoint(pos):
                        self._go_category()
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
            if self.round_data["move_dir"] != 0:
                self.round_data["basket_x"] += self.round_data["move_dir"] * 8
                self.round_data["basket_x"] = max(self.play_area.left + 60, min(self.play_area.right - 60, self.round_data["basket_x"]))
            self.round_data["fruit_y"] += self.round_data["fruit_speed"]
            if self.round_data["fruit_y"] >= self.play_area.bottom - 46:
                success = abs(self.round_data["fruit_x"] - self.round_data["basket_x"]) <= 70 and self._clarity() >= 0.55
                self._resolve_catch(success)
            if self.session.is_complete():
                self._finish_game()
                return
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
