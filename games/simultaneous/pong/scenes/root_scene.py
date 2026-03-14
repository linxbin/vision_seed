import random
import time
from datetime import datetime

import pygame

from core.asset_loader import load_image_if_exists, project_path
from core.base_scene import BaseScene
from games.common.anaglyph import BLUE_FILTER, FILTER_LR, FILTER_RL, GLASSES_BACKGROUND, GLASSES_BUTTON_COLOR, MODE_GLASSES, RED_FILTER


class PongScene(BaseScene):
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
        self.player_move = 0
        self.feedback_text = ""
        self.feedback_until = 0.0
        self.feedback_color = (86, 158, 108)
        self.hit_flash_until = 0.0
        self.hit_flash_side = None
        self.best_rally = 0
        self.current_rally = 0
        self.player_score = 0
        self.ai_score = 0
        self.player_hits = 0
        self.session_started_at = 0.0
        self.serve_until = 0.0
        self.serve_direction = 1
        self.final_stats = {}
        self._refresh_fonts()
        self._build_ui()
        self._reset_match()

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
        self.play_rect = pygame.Rect(72, 120, self.width - 144, self.height - 220)

    def on_resize(self, width, height):
        self.width = width
        self.height = height
        self._build_ui()
        self._reset_match()

    def reset(self):
        self.state = self.STATE_HOME
        self.mode = self.MODE_NAKED
        self.filter_direction = self.FILTER_LR
        self.show_filter_picker = False
        self.home_focus = 0
        self.result_focus = 0
        self.feedback_text = ""
        self._reset_match()

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

    def _draw_wrapped_text(self, screen, text, font, color, topleft, max_width, line_gap=6):
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

    def _reset_match(self):
        self.player_y = self.play_rect.centery - 48
        self.ai_y = self.play_rect.centery - 48
        self.ball_x = self.play_rect.centerx
        self.ball_y = self.play_rect.centery
        self.ball_vx = random.choice((-5.0, 5.0))
        self.ball_vy = random.choice((-3.0, -2.2, 2.2, 3.0))
        self.best_rally = 0
        self.current_rally = 0
        self.player_score = 0
        self.ai_score = 0
        self.player_hits = 0
        self.serve_until = 0.0
        self.serve_direction = 1

    def _start_match(self):
        self.state = self.STATE_PLAY
        self.session_started_at = time.time()
        self.feedback_text = ""
        self._reset_match()
        self._start_serve(1)

    def _go_category(self):
        self.manager.set_scene("category")

    def _go_menu(self):
        self.manager.set_scene("menu")

    def _set_feedback(self, key, duration=1.0):
        self.feedback_text = self.manager.t(key)
        self.feedback_until = time.time() + duration
        self.feedback_color = (86, 158, 108)

    def _set_feedback_text(self, text, color=(86, 158, 108), duration=0.8):
        self.feedback_text = text
        self.feedback_color = color
        self.feedback_until = time.time() + duration

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

    def _start_serve(self, direction):
        self.ball_x, self.ball_y = self.play_rect.center
        self.ball_vx = 5.0 * (1 if direction >= 0 else -1)
        self.ball_vy = random.choice((-3.2, -2.4, 2.4, 3.2))
        self.serve_direction = 1 if direction >= 0 else -1
        self.serve_until = time.time() + 1.0

    def _serve_countdown(self):
        remaining = max(0.0, self.serve_until - time.time())
        return int(remaining) + (1 if remaining > int(remaining) else 0)

    def _result_encouragement(self):
        if self.player_score > self.ai_score:
            return self.manager.t("pong.result.encourage.win")
        if self.best_rally >= 6:
            return self.manager.t("pong.result.encourage.rally")
        return self.manager.t("pong.result.encourage.keep")

    def _finish_match(self):
        self.state = self.STATE_RESULT
        duration = int(max(0, time.time() - self.session_started_at))
        self.final_stats = {
            "duration": duration,
            "player_score": self.player_score,
            "ai_score": self.ai_score,
            "player_hits": self.player_hits,
            "best_rally": self.best_rally,
            "accuracy": round((self.player_hits / max(1, self.player_hits + self.ai_score)) * 100, 1),
            "encouragement": self._result_encouragement(),
            "mode": self.mode,
            "filter_direction": self.filter_direction,
        }
        self._save_result()

    def _save_result(self):
        data_manager = getattr(self.manager, "data_manager", None)
        if not data_manager:
            return
        total = self.player_score + self.ai_score
        accuracy = round((self.player_score / total) * 100, 1) if total else 0.0
        payload = {
            "timestamp": datetime.now().isoformat(),
            "game_id": "simultaneous.pong",
            "difficulty_level": 3,
            "total_questions": total,
            "correct_count": self.player_score,
            "wrong_count": self.ai_score,
            "duration_seconds": float(self.final_stats.get("duration", 0)),
            "accuracy_rate": self.final_stats.get("accuracy", accuracy),
            "training_metrics": {
                "pong_best_rally": self.best_rally,
                "player_hits": self.player_hits,
                "return_accuracy": self.final_stats.get("accuracy", accuracy),
            },
        }
        data_manager.save_training_session(payload)

    def _player_paddle_rect(self):
        return pygame.Rect(self.play_rect.left + 26, int(self.player_y), 16, 96)

    def _ai_paddle_rect(self):
        return pygame.Rect(self.play_rect.right - 42, int(self.ai_y), 16, 96)

    def _ball_rect(self):
        return pygame.Rect(int(self.ball_x - 10), int(self.ball_y - 10), 20, 20)

    def _left_color(self):
        return RED_FILTER[:3] if self.filter_direction == self.FILTER_LR else BLUE_FILTER[:3]

    def _right_color(self):
        return BLUE_FILTER[:3] if self.filter_direction == self.FILTER_LR else RED_FILTER[:3]

    def handle_events(self, events):
        for event in events:
            if self.show_filter_picker:
                if event.type == pygame.KEYDOWN:
                    if event.key in (pygame.K_LEFT, pygame.K_RIGHT):
                        self.filter_direction = self.FILTER_RL if self.filter_direction == self.FILTER_LR else self.FILTER_LR
                    elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
                        self.show_filter_picker = False
                        self._start_match()
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
                        self._start_match()
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
                            self._start_match()
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
                        self._start_match()
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
                    elif event.key == pygame.K_UP:
                        self.player_move = -1
                    elif event.key == pygame.K_DOWN:
                        self.player_move = 1
                elif event.type == pygame.KEYUP:
                    if event.key == pygame.K_UP and self.player_move < 0:
                        self.player_move = 0
                    elif event.key == pygame.K_DOWN and self.player_move > 0:
                        self.player_move = 0
                elif event.type == pygame.MOUSEMOTION:
                    self.player_y = max(self.play_rect.top, min(self.play_rect.bottom - 96, event.pos[1] - 48))
                elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1 and self.btn_home.collidepoint(getattr(event, "pos", pygame.mouse.get_pos())):
                    self._go_category()
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
            elapsed = now - self.session_started_at
            if elapsed >= self._session_seconds() or self.player_score >= 11 or self.ai_score >= 11:
                self._finish_match()
                return
            self.player_y = max(self.play_rect.top, min(self.play_rect.bottom - 96, self.player_y + self.player_move * 7))
            target_ai = self.ball_y - 48
            self.ai_y += max(-5, min(5, target_ai - self.ai_y))
            self.ai_y = max(self.play_rect.top, min(self.play_rect.bottom - 96, self.ai_y))
            if self.serve_until > now:
                return
            self.ball_x += self.ball_vx
            self.ball_y += self.ball_vy
            if self.ball_y <= self.play_rect.top + 10 or self.ball_y >= self.play_rect.bottom - 10:
                self.ball_vy *= -1
            if self._ball_rect().colliderect(self._player_paddle_rect()) and self.ball_vx < 0:
                self.ball_vx = min(8.6, abs(self.ball_vx) * 1.06)
                self.ball_vy = max(-6.2, min(6.2, self.ball_vy + random.choice((-0.5, 0.5))))
                self.current_rally += 1
                self.player_hits += 1
                self.best_rally = max(self.best_rally, self.current_rally)
                self.hit_flash_side = "left"
                self.hit_flash_until = now + 0.18
                if self.current_rally > 0 and self.current_rally % 4 == 0:
                    self._set_feedback("pong.feedback.combo", 0.8)
                elif self.current_rally >= 2:
                    self._set_feedback_text(self.manager.t("pong.feedback.rally", n=self.current_rally), duration=0.55)
            if self._ball_rect().colliderect(self._ai_paddle_rect()) and self.ball_vx > 0:
                self.ball_vx = -min(8.6, abs(self.ball_vx) * 1.06)
                self.ball_vy = max(-6.2, min(6.2, self.ball_vy + random.choice((-0.5, 0.5))))
                self.current_rally += 1
                self.best_rally = max(self.best_rally, self.current_rally)
                self.hit_flash_side = "right"
                self.hit_flash_until = now + 0.18
            if self.ball_x < self.play_rect.left:
                self.ai_score += 1
                self.current_rally = 0
                self._set_feedback_text(self.manager.t("pong.feedback.miss"), color=(232, 110, 110), duration=0.8)
                self._start_serve(1)
            elif self.ball_x > self.play_rect.right:
                self.player_score += 1
                self.current_rally = 0
                self._set_feedback("pong.feedback.point", 0.8)
                self._start_serve(-1)
        if self.feedback_text and now > self.feedback_until:
            self.feedback_text = ""
        if self.hit_flash_until and now > self.hit_flash_until:
            self.hit_flash_side = None
            self.hit_flash_until = 0.0

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

    def _draw_home(self, screen):
        title = self.title_font.render(self.manager.t("pong.title"), True, (34, 60, 96))
        subtitle = self.sub_font.render(self.manager.t("pong.subtitle"), True, (86, 104, 130))
        screen.blit(title, (self.width // 2 - title.get_width() // 2, 82))
        screen.blit(subtitle, (self.width // 2 - subtitle.get_width() // 2, 138))
        self._draw_button(screen, self.btn_naked, self.manager.t("pong.home.naked"), (96, 140, 214), selected=self.home_focus == 0)
        self._draw_button(screen, self.btn_glasses, self.manager.t("pong.home.glasses"), GLASSES_BUTTON_COLOR, selected=self.home_focus == 1)
        self._draw_button(screen, self.btn_help, self.manager.t("pong.home.help"), (124, 140, 168), icon_name="question", selected=self.home_focus == 2)
        self._draw_button(screen, self.btn_back, self.manager.t("common.back"), (86, 116, 170), icon_name="back_arrow", selected=self.home_focus == 3)

    def _draw_help(self, screen):
        title = self.title_font.render(self.manager.t("pong.help.title"), True, (34, 60, 96))
        screen.blit(title, (self.width // 2 - title.get_width() // 2, 68))
        steps = [
            self.manager.t("pong.help.step1"),
            self.manager.t("pong.help.step2"),
            self.manager.t("pong.help.step3"),
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
            self._draw_wrapped_text(screen, text, self.body_font, (72, 90, 116), (card.x + 162, card.y + 18), card.width - 184, line_gap=4)
        self._draw_button(screen, self.help_ok, self.manager.t("pong.help.ok"), (244, 208, 120), text_color=(92, 76, 34), icon_name="check")

    def _draw_help_illustration(self, screen, idx, card):
        area = pygame.Rect(card.x + 64, card.y + 16, 78, card.height - 32)
        pygame.draw.rect(screen, (232, 241, 252), area, border_radius=14)
        if idx == 0:
            left = pygame.Rect(area.x + 8, area.y + 10, 18, area.height - 20)
            right = pygame.Rect(area.right - 26, area.y + 10, 18, area.height - 20)
            pygame.draw.rect(screen, RED_FILTER[:3], left, border_radius=8)
            pygame.draw.rect(screen, BLUE_FILTER[:3], right, border_radius=8)
            pygame.draw.circle(screen, (255, 226, 96), area.center, 9)
        elif idx == 1:
            paddle = pygame.Rect(area.centerx - 8, area.y + 8, 16, area.height - 16)
            pygame.draw.rect(screen, (96, 140, 214), paddle, border_radius=8)
            arrow_up = [(area.x + 12, area.centery - 8), (area.x + 24, area.centery - 20), (area.x + 36, area.centery - 8)]
            arrow_down = [(area.x + 12, area.centery + 8), (area.x + 24, area.centery + 20), (area.x + 36, area.centery + 8)]
            pygame.draw.lines(screen, (92, 106, 132), False, arrow_up, 3)
            pygame.draw.lines(screen, (92, 106, 132), False, arrow_down, 3)
        else:
            pygame.draw.rect(screen, (96, 140, 214), (area.x + 6, area.y + 10, 14, area.height - 20), border_radius=7)
            pygame.draw.rect(screen, (136, 156, 196), (area.right - 20, area.y + 10, 14, area.height - 20), border_radius=7)
            pygame.draw.circle(screen, (255, 226, 96), (area.centerx, area.centery), 8)
            pygame.draw.arc(screen, (120, 188, 124), pygame.Rect(area.x + 10, area.y + 10, area.width - 20, area.height - 20), 0.4, 2.7, 3)

    def _draw_filter_picker(self, screen):
        overlay = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        overlay.fill((24, 32, 46, 136))
        screen.blit(overlay, (0, 0))
        pygame.draw.rect(screen, (249, 251, 255), self.filter_modal, border_radius=18)
        pygame.draw.rect(screen, (190, 206, 228), self.filter_modal, 2, border_radius=18)
        title = self.sub_font.render(self.manager.t("pong.filter.pick"), True, (52, 70, 100))
        screen.blit(title, (self.filter_modal.centerx - title.get_width() // 2, self.filter_modal.y + 20))
        self._draw_filter_option(screen, self.filter_lr, self.manager.t("pong.filter.lr"), RED_FILTER[:3], BLUE_FILTER[:3], self.filter_direction == self.FILTER_LR)
        self._draw_filter_option(screen, self.filter_rl, self.manager.t("pong.filter.rl"), BLUE_FILTER[:3], RED_FILTER[:3], self.filter_direction == self.FILTER_RL)
        self._draw_button(screen, self.filter_start, self.manager.t("pong.filter.start"), (92, 152, 114), icon_name="check")

    def _draw_play(self, screen):
        chip = pygame.Rect(self.width // 2 - 106, 18, 212, 38)
        time_left = max(0, int(self._session_seconds() - (time.time() - self.session_started_at)))
        self._draw_chip(screen, chip, self.manager.t("pong.time", sec=f"{time_left // 60:02d}:{time_left % 60:02d}"), (86, 116, 170))
        score_text = self.body_font.render(self.manager.t("pong.score", player=self.player_score, ai=self.ai_score), True, (44, 60, 88))
        screen.blit(score_text, (84, 22))
        rally_text = self.body_font.render(
            self.manager.t("pong.rally", n=self.current_rally),
            True,
            (88, 72, 32),
        )
        screen.blit(rally_text, (84, 58))
        best_rally_text = self.body_font.render(
            self.manager.t("pong.best_rally", n=self.best_rally),
            True,
            (92, 102, 120),
        )
        screen.blit(best_rally_text, (self.width - 124 - best_rally_text.get_width(), 26))
        guide = self.small_font.render(self.manager.t("pong.play.guide"), True, (54, 70, 96))
        screen.blit(guide, (self.width // 2 - guide.get_width() // 2, 68))
        self._draw_button(screen, self.btn_home, self.manager.t("common.back"), (86, 116, 170), icon_name="back_arrow")
        for y in range(self.play_rect.top, self.play_rect.bottom, 28):
            pygame.draw.line(screen, (200, 210, 226), (self.play_rect.centerx, y), (self.play_rect.centerx, min(y + 16, self.play_rect.bottom)), 2)
        left_color = self._left_color() if self.mode == self.MODE_GLASSES else (96, 140, 214)
        right_color = self._right_color() if self.mode == self.MODE_GLASSES else (136, 156, 196)
        if self.hit_flash_side == "left":
            left_color = tuple(min(255, c + 45) for c in left_color)
        if self.hit_flash_side == "right":
            right_color = tuple(min(255, c + 45) for c in right_color)
        pygame.draw.rect(screen, left_color, self._player_paddle_rect(), border_radius=8)
        pygame.draw.rect(screen, right_color, self._ai_paddle_rect(), border_radius=8)
        pygame.draw.circle(screen, (255, 226, 96), (int(self.ball_x), int(self.ball_y)), 10)
        if self.serve_until > time.time():
            serve_text = self.body_font.render(self.manager.t("pong.serve", n=self._serve_countdown()), True, (56, 68, 94))
            screen.blit(serve_text, (self.width - 84 - serve_text.get_width(), 56))
        if self.feedback_text:
            feedback = self.body_font.render(self.feedback_text, True, self.feedback_color)
            screen.blit(feedback, (self.width // 2 - feedback.get_width() // 2, self.height - 76))

    def _draw_result(self, screen):
        title = self.title_font.render(self.manager.t("pong.result.title"), True, (34, 60, 96))
        screen.blit(title, (self.width // 2 - title.get_width() // 2, 74))
        mode_text = self.manager.t("pong.mode.naked") if self.final_stats.get("mode") == self.MODE_NAKED else self.manager.t("pong.mode.glasses")
        filter_text = "-"
        if self.final_stats.get("mode") == self.MODE_GLASSES:
            filter_text = self.manager.t("pong.filter.lr") if self.final_stats.get("filter_direction") == self.FILTER_LR else self.manager.t("pong.filter.rl")
        lines = [
            self.manager.t("pong.result.score", player=self.final_stats.get("player_score", 0), ai=self.final_stats.get("ai_score", 0)),
            self.manager.t("pong.result.duration", sec=self.final_stats.get("duration", 0)),
            self.manager.t("pong.result.player_hits", n=self.final_stats.get("player_hits", 0)),
            self.manager.t("pong.result.ai_points", n=self.final_stats.get("ai_score", 0)),
            self.manager.t("pong.result.accuracy", value=self.final_stats.get("accuracy", 0.0)),
            self.manager.t("pong.result.mode", mode=mode_text),
            self.manager.t("pong.result.filter", direction=filter_text),
            self.manager.t("pong.result.metric", n=self.final_stats.get("best_rally", 0)),
        ]
        for idx, text in enumerate(lines):
            line = self.body_font.render(text, True, (66, 84, 114))
            screen.blit(line, (self.width // 2 - line.get_width() // 2, 164 + idx * 34))
        encouragement = self.body_font.render(self.final_stats.get("encouragement", ""), True, (88, 118, 82))
        screen.blit(encouragement, (self.width // 2 - encouragement.get_width() // 2, 428))
        self._draw_button(screen, self.btn_continue, self.manager.t("pong.result.continue"), (84, 148, 108), icon_name="check", selected=self.result_focus == 0)
        self._draw_button(screen, self.btn_exit, self.manager.t("pong.result.exit"), (120, 134, 168), icon_name="cross", selected=self.result_focus == 1)

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
