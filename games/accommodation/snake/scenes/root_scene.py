import time
from datetime import datetime

import pygame

from core.base_scene import BaseScene
from ..services import SnakeBoardService, SnakeScoringService, SnakeSessionService


class SnakeFocusScene(BaseScene):
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
        self.board_service = SnakeBoardService()
        self.scoring = SnakeScoringService()
        self.session = SnakeSessionService(self._session_seconds())
        self.tick_at = time.time()
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
        top = (240, 248, 233)
        bottom = (222, 240, 218)
        for y in range(self.height):
            t = y / max(1, self.height - 1)
            color = (int(top[0] * (1 - t) + bottom[0] * t), int(top[1] * (1 - t) + bottom[1] * t), int(top[2] * (1 - t) + bottom[2] * t))
            pygame.draw.line(screen, color, (0, y), (self.width, y))

    def _set_feedback(self, key, color):
        self.feedback_text = self.manager.t(key)
        self.feedback_color = color
        self.feedback_until = time.time() + 1.0

    def _start_game(self):
        self.state = self.STATE_PLAY
        self.scoring.reset()
        self.session.session_seconds = self._session_seconds()
        self.session.start()
        self.round_data = self.board_service.create_round(self.play_area)
        self.tick_at = time.time()

    def _finish_game(self):
        self.state = self.STATE_RESULT
        self.final_stats = {
            "duration": int(self.session.session_elapsed),
            "success": self.scoring.food_count,
            "wrong": self.scoring.collision_count,
            "accuracy": self.scoring.accuracy(),
            "score": self.scoring.score,
            "best_length": self.scoring.best_length,
        }
        if getattr(self.manager, "data_manager", None):
            self.manager.data_manager.save_training_session({
                "timestamp": datetime.now().isoformat(),
                "game_id": "accommodation.snake",
                "difficulty_level": 3,
                "total_questions": self.scoring.total_steps,
                "correct_count": self.scoring.safe_steps,
                "wrong_count": self.scoring.collision_count,
                "duration_seconds": float(self.final_stats["duration"]),
                "accuracy_rate": self.final_stats["accuracy"],
                "training_metrics": {
                    "best_length": self.final_stats["best_length"],
                    "foods_eaten": self.final_stats["success"],
                },
            })
        self.play_completed_sound()

    def _speed_seconds(self):
        progress = min(1.0, self.session.session_elapsed / max(1, self.session.session_seconds)) if self.session.session_seconds else 0.0
        return 0.22 if progress < 0.34 else 0.17 if progress < 0.67 else 0.13

    def _inner_board_rect(self):
        return self.play_area.inflate(-8, -8)

    def _step_snake(self):
        direction = self.round_data["pending_direction"]
        head_x, head_y = self.round_data["snake"][0]
        next_head = (head_x + direction[0], head_y + direction[1])
        snake = self.round_data["snake"]
        if next_head[0] < 0 or next_head[1] < 0 or next_head[0] >= self.round_data["cols"] or next_head[1] >= self.round_data["rows"] or next_head in snake[:-1]:
            self.scoring.on_collision()
            self.play_wrong_sound()
            self._set_feedback("snake_focus.feedback.crash", (214, 96, 96))
            self.round_data = self.board_service.create_round(self.play_area)
            return
        snake.insert(0, next_head)
        if next_head == self.round_data["food"]:
            self.scoring.on_food(len(snake))
            self.play_correct_sound()
            self._set_feedback("snake_focus.feedback.food", (86, 174, 112))
            self.round_data["food"] = self.board_service._spawn_food(self.round_data["cols"], self.round_data["rows"], snake)
        else:
            snake.pop()
            self.scoring.on_step(len(snake))
        self.round_data["direction"] = direction

    def _draw_home(self, screen):
        title = self.title_font.render(self.manager.t("snake_focus.title"), True, (56, 108, 68))
        screen.blit(title, (self.width // 2 - title.get_width() // 2, 86))
        self._draw_button(screen, self.btn_start, self.manager.t("snake_focus.home.start"), (96, 156, 104))
        self._draw_button(screen, self.btn_help, self.manager.t("snake_focus.home.help"), (126, 142, 174))
        self._draw_button(screen, self.btn_back, self.manager.t("common.back"), (88, 116, 168))

    def _draw_help(self, screen):
        title = self.title_font.render(self.manager.t("snake_focus.help.title"), True, (42, 96, 58))
        screen.blit(title, (self.width // 2 - title.get_width() // 2, 76))
        for idx, key in enumerate(("snake_focus.help.step1", "snake_focus.help.step2", "snake_focus.help.step3")):
            card = pygame.Rect(90, 170 + idx * 104, self.width - 180, 88)
            pygame.draw.rect(screen, (246, 250, 255), card, border_radius=16)
            pygame.draw.rect(screen, (196, 212, 234), card, 2, border_radius=16)
            self._draw_wrapped_text(screen, f"{idx + 1}. {self.manager.t(key)}", card.x + 20, card.y + 16, card.width - 40)
        self._draw_button(screen, self.help_ok, self.manager.t("snake_focus.help.ok"), (242, 214, 126), text_color=(104, 84, 42))

    def _draw_play(self, screen):
        remaining = max(0, int(self.session.session_seconds - self.session.session_elapsed))
        progress = min(1.0, self.session.session_elapsed / max(1, self.session.session_seconds)) if self.session.session_seconds else 0.0
        timer = self.body_font.render(self.manager.t("snake_focus.time", sec=f"{remaining // 60:02d}:{remaining % 60:02d}"), True, (222, 74, 74) if remaining <= 30 else (65, 110, 72))
        score = self.body_font.render(self.manager.t("snake_focus.score", score=self.scoring.score), True, (65, 110, 72))
        stage = self.small_font.render(self.manager.t(self.board_service.stage_label_key(progress)), True, (84, 110, 96))
        goal = self.small_font.render(self.manager.t(self.board_service.goal_label_key(progress)), True, (84, 110, 96))
        guide = self.small_font.render(self.manager.t("snake_focus.play.guide"), True, (84, 110, 96))
        screen.blit(self.body_font.render(self.manager.t("snake_focus.mode.naked"), True, (65, 110, 72)), (24, 18))
        screen.blit(timer, (self.width // 2 - timer.get_width() // 2, 14))
        screen.blit(score, (self.width // 2 - score.get_width() // 2, 44))
        screen.blit(stage, (self.play_area.x, 98))
        screen.blit(goal, (self.play_area.right - goal.get_width(), 98))
        screen.blit(guide, (self.play_area.centerx - guide.get_width() // 2, self.play_area.y - 26))
        inner_board = self._inner_board_rect()
        pygame.draw.rect(screen, (240, 248, 233), inner_board, border_radius=10)
        cell = self.board_service.CELL
        for x in range(self.round_data["cols"]):
            for y in range(self.round_data["rows"]):
                rect = pygame.Rect(inner_board.x + x * cell, inner_board.y + y * cell, cell, cell)
                if (x + y) % 2 == 0:
                    pygame.draw.rect(screen, (228, 241, 220), rect)
        food = self.round_data["food"]
        food_rect = pygame.Rect(inner_board.x + food[0] * cell + 4, inner_board.y + food[1] * cell + 4, cell - 8, cell - 8)
        pygame.draw.ellipse(screen, (238, 92, 92), food_rect)
        for index, segment in enumerate(self.round_data["snake"]):
            color = (72, 138, 84) if index == 0 else (104, 178, 116)
            rect = pygame.Rect(inner_board.x + segment[0] * cell + 3, inner_board.y + segment[1] * cell + 3, cell - 6, cell - 6)
            pygame.draw.rect(screen, color, rect, border_radius=8)
        pygame.draw.rect(screen, (176, 204, 176), inner_board, 2, border_radius=10)
        if self.feedback_text and time.time() <= self.feedback_until:
            fb = self.body_font.render(self.feedback_text, True, self.feedback_color)
            screen.blit(fb, (self.width // 2 - fb.get_width() // 2, inner_board.bottom + 20))
        self._draw_button(screen, self.btn_home, self.manager.t("common.back"), (88, 116, 168))

    def _draw_result(self, screen):
        title = self.title_font.render(self.manager.t("snake_focus.result.title"), True, (42, 96, 58))
        screen.blit(title, (self.width // 2 - title.get_width() // 2, 100))
        lines = [
            self.manager.t("snake_focus.result.duration", sec=self.final_stats.get("duration", 0)),
            self.manager.t("snake_focus.result.success", n=self.final_stats.get("success", 0)),
            self.manager.t("snake_focus.result.wrong", n=self.final_stats.get("wrong", 0)),
            self.manager.t("snake_focus.result.accuracy", value=self.final_stats.get("accuracy", 0.0)),
            self.manager.t("snake_focus.result.score", n=self.final_stats.get("score", 0)),
            self.manager.t("snake_focus.result.length", n=self.final_stats.get("best_length", 0)),
        ]
        for idx, text in enumerate(lines):
            line = self.body_font.render(text, True, (58, 84, 118))
            screen.blit(line, (self.width // 2 - line.get_width() // 2, 176 + idx * 34))
        self._draw_button(screen, self.btn_continue, self.manager.t("snake_focus.result.continue"), (84, 148, 108))
        self._draw_button(screen, self.btn_exit, self.manager.t("snake_focus.result.exit"), (120, 134, 168))

    def handle_events(self, events):
        reverse = {(1, 0): (-1, 0), (-1, 0): (1, 0), (0, 1): (0, -1), (0, -1): (0, 1)}
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
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        self.manager.set_scene("category")
                    direction = None
                    if event.key == pygame.K_LEFT:
                        direction = (-1, 0)
                    elif event.key == pygame.K_RIGHT:
                        direction = (1, 0)
                    elif event.key == pygame.K_UP:
                        direction = (0, -1)
                    elif event.key == pygame.K_DOWN:
                        direction = (0, 1)
                    if direction and direction != reverse.get(self.round_data["direction"]):
                        self.round_data["pending_direction"] = direction
                elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1 and self.btn_home.collidepoint(getattr(event, "pos", pygame.mouse.get_pos())):
                    self.manager.set_scene("category")
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
            if self.session.is_complete():
                self._finish_game()
                return
            if now - self.tick_at >= self._speed_seconds():
                self.tick_at = now
                self._step_snake()
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
