import math
import time

import pygame

from core.asset_loader import load_image_if_exists, project_path
from core.base_scene import BaseScene
from ..services import EyeFindPatternService, EyeFindScoringService, EyeFindSessionService


class EyeFindPatternsScene(BaseScene):
    STATE_HOME = "home"
    STATE_HELP = "help"
    STATE_PLAY = "play"
    STATE_RESULT = "result"

    MODE_NAKED = "naked"
    MODE_GLASSES = "glasses"

    FILTER_LR = "left_red_right_blue"
    FILTER_RL = "left_blue_right_red"

    ATTEMPT_SECONDS = 30
    OVERLAP_TOLERANCE = 8

    def __init__(self, manager):
        super().__init__(manager)
        self._refresh_fonts()
        self.width = 900
        self.height = 700

        self.state = self.STATE_HOME
        self.mode = self.MODE_NAKED
        self.filter_direction = self.FILTER_LR
        self.show_filter_picker = False

        self.pattern_service = EyeFindPatternService()
        self.scoring = EyeFindScoringService()
        self.session = EyeFindSessionService(self._session_seconds(), self.ATTEMPT_SECONDS)
        self.final_stats = {}

        self.left_center = (0, 0)
        self.right_center = (0, 0)
        self.dragging_right = False
        self.drag_offset = (0, 0)
        self.pattern_surface = pygame.Surface((1, 1), pygame.SRCALPHA)
        self.pattern_id = "star"
        self.pattern_color = (255, 214, 140, 255)
        self.session_elapsed = 0.0
        self.attempt_elapsed = 0.0
        self.feedback_text = ""
        self.feedback_color = (255, 255, 255)
        self.feedback_until = 0.0

        self._build_ui_rects()
        self._new_pattern(reset_position=True)

    def _refresh_fonts(self):
        self.title_font = self.create_font(56)
        self.sub_font = self.create_font(26)
        self.option_font = self.create_font(30)
        self.body_font = self.create_font(22)
        self.small_font = self.create_font(18)
        self.tiny_font = self.create_font(16)

    def _build_ui_rects(self):
        card_w = min(560, self.width - 120)
        card_h = 62
        start_x = self.width // 2 - card_w // 2
        start_y = 210
        gap = 16
        self.btn_naked = pygame.Rect(start_x, start_y, card_w, card_h)
        self.btn_glasses = pygame.Rect(start_x, start_y + card_h + gap, card_w, card_h)
        self.btn_help = pygame.Rect(start_x, start_y + (card_h + gap) * 2, card_w, card_h)
        self.btn_back = pygame.Rect(self.width - 108, 18, 88, 36)

        self.btn_confirm = pygame.Rect(self.width // 2 - 94, self.height - 58, 188, 44)
        self.btn_continue = pygame.Rect(self.width // 2 - 210, self.height - 100, 180, 48)
        self.btn_exit = pygame.Rect(self.width // 2 + 30, self.height - 100, 180, 48)
        self.btn_home = pygame.Rect(self.width - 110, 16, 88, 36)

        self.filter_modal = pygame.Rect(self.width // 2 - 250, self.height // 2 - 128, 500, 220)
        self.filter_lr = pygame.Rect(self.filter_modal.x + 24, self.filter_modal.y + 68, 210, 46)
        self.filter_rl = pygame.Rect(self.filter_modal.x + 266, self.filter_modal.y + 68, 210, 46)
        self.filter_start = pygame.Rect(self.filter_modal.centerx - 90, self.filter_modal.y + 150, 180, 44)

        self.help_ok = pygame.Rect(self.width // 2 - 90, self.height - 90, 180, 54)
        self.play_area = pygame.Rect(80, 120, self.width - 160, self.height - 300)
        self.left_center = (self.width // 2 - 140, self.height // 2 + 10)
        self.right_center = (self.width // 2 + 140, self.height // 2 + 10)

    def on_resize(self, width, height):
        self.width = width
        self.height = height
        self._build_ui_rects()

    def reset(self):
        self.state = self.STATE_HOME
        self.mode = self.MODE_NAKED
        self.filter_direction = self.FILTER_LR
        self.show_filter_picker = False
        self.feedback_text = ""
        self.session_elapsed = 0.0
        self.attempt_elapsed = 0.0
        self.scoring.reset()
        self.session.reset()
        self._new_pattern(reset_position=True)

    def _session_seconds(self):
        try:
            minutes = int(self.manager.settings.get("session_duration_minutes", 5))
        except (TypeError, ValueError):
            minutes = 5
        return max(60, minutes * 60)

    def _exit_to_main_menu(self):
        self.manager.set_scene("menu")

    def _start_game(self):
        self.state = self.STATE_PLAY
        self.scoring.reset()
        self.session.session_seconds = self._session_seconds()
        self.session.start()
        self.session_elapsed = 0.0
        self.attempt_elapsed = 0.0
        self.feedback_text = ""
        self._new_pattern(reset_position=True)

    def _finish_game(self):
        self.state = self.STATE_RESULT
        self.final_stats = self.session.build_final_stats(self.scoring, self.mode, self.filter_direction)
        self.scoring.reset()

    def _set_feedback(self, key, color):
        self.feedback_text = self.manager.t(key)
        self.feedback_color = color
        self.feedback_until = time.time() + 1.2

    def _new_pattern(self, reset_position):
        pattern = self.pattern_service.next_pattern(size=140)
        self.pattern_id = pattern["pattern_id"]
        self.pattern_color = pattern["color"]
        self.pattern_surface = pattern["surface"]
        if reset_position:
            self.left_center, self.right_center = self.pattern_service.reset_positions(self.width, self.height)

    def _apply_filter(self, base, side):
        return self.pattern_service.apply_filter(base, self.mode, self.filter_direction, side, self.MODE_GLASSES, self.FILTER_LR)

    def _is_overlapped(self):
        dx = self.left_center[0] - self.right_center[0]
        dy = self.left_center[1] - self.right_center[1]
        return math.hypot(dx, dy) <= self.OVERLAP_TOLERANCE

    def _confirm_action(self):
        if self._is_overlapped():
            gained = self.scoring.on_success()
            self._set_feedback("eye_find.success", (90, 226, 132))
            if gained > EyeFindScoringService.BASE_SCORE:
                self.feedback_text = f"{self.feedback_text}  +{gained}"
            self.session.restart_attempt()
            self._new_pattern(reset_position=True)
        else:
            self.scoring.on_failure()
            self._set_feedback("eye_find.fail", (238, 118, 118))

    def _draw_gradient_bg(self, screen):
        if self.state == self.STATE_PLAY and self.mode == self.MODE_GLASSES:
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
            overlay = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
            overlay.fill(self.pattern_service.GLASSES_BACKGROUND)
            screen.blit(overlay, (0, 0))
            return
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
        now = time.time()
        for i in range(4):
            cx = int((self.width * (0.2 + i * 0.2) + math.sin(now * (0.15 + i * 0.03)) * 28))
            cy = int(90 + i * 34 + math.cos(now * (0.2 + i * 0.05)) * 8)
            pygame.draw.circle(screen, (245, 250, 255), (cx, cy), 26)
            pygame.draw.circle(screen, (238, 246, 255), (cx + 22, cy + 8), 20)

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
            text_surface = self.option_font.render(text, True, text_color)
            use_light_icon = sum(text_color) > 500
            icon = self._load_ui_icon(icon_name, light=use_light_icon) if icon_name else None
            gap = 8 if icon is not None else 0
            content_width = text_surface.get_width() + (icon.get_width() + gap if icon is not None else 0)
            start_x = rect.centerx - content_width // 2
            if icon is not None:
                screen.blit(icon, (start_x, rect.centery - icon.get_height() // 2))
                start_x += icon.get_width() + gap
            screen.blit(
                text_surface,
                (start_x, rect.centery - text_surface.get_height() // 2),
            )
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
            text_surface = pygame.transform.smoothscale(
                text_surface,
                (max(1, max_text_width), text_surface.get_height()),
            )
        screen.blit(text_surface, (text_x, text_y))

    def _format_time(self, sec):
        s = max(0, int(sec))
        return f"{s // 60:02d}:{s % 60:02d}"

    def handle_events(self, events):
        for event in events:
            if self.state == self.STATE_HOME:
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        self.manager.set_scene("category")
                    elif event.key == pygame.K_1:
                        self.mode = self.MODE_NAKED
                        self._start_game()
                    elif event.key == pygame.K_2:
                        self.mode = self.MODE_GLASSES
                        self.show_filter_picker = True
                    elif event.key == pygame.K_3:
                        self.state = self.STATE_HELP
                    elif event.key == pygame.K_RETURN and self.show_filter_picker:
                        self.show_filter_picker = False
                        self._start_game()
                elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    pos = getattr(event, "pos", pygame.mouse.get_pos())
                    if self.show_filter_picker:
                        if self.filter_lr.collidepoint(pos):
                            self.filter_direction = self.FILTER_LR
                        elif self.filter_rl.collidepoint(pos):
                            self.filter_direction = self.FILTER_RL
                        elif self.filter_start.collidepoint(pos):
                            self.show_filter_picker = False
                            self._start_game()
                        continue
                    if self.btn_back.collidepoint(pos):
                        self.manager.set_scene("category")
                    elif self.btn_naked.collidepoint(pos):
                        self.mode = self.MODE_NAKED
                        self._start_game()
                    elif self.btn_glasses.collidepoint(pos):
                        self.mode = self.MODE_GLASSES
                        self.show_filter_picker = True
                    elif self.btn_help.collidepoint(pos):
                        self.state = self.STATE_HELP

            elif self.state == self.STATE_HELP:
                if event.type == pygame.KEYDOWN and event.key in (pygame.K_ESCAPE, pygame.K_RETURN):
                    self.state = self.STATE_HOME
                elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    pos = getattr(event, "pos", pygame.mouse.get_pos())
                    if self.help_ok.collidepoint(pos):
                        self.state = self.STATE_HOME

            elif self.state == self.STATE_PLAY:
                if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                    self._exit_to_main_menu()
                elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    pos = getattr(event, "pos", pygame.mouse.get_pos())
                    right_rect = self.pattern_surface.get_rect(center=self.right_center)
                    if self.btn_home.collidepoint(pos):
                        self._exit_to_main_menu()
                    elif self.btn_confirm.collidepoint(pos):
                        self._confirm_action()
                    elif right_rect.collidepoint(pos):
                        self.dragging_right = True
                        self.drag_offset = (self.right_center[0] - pos[0], self.right_center[1] - pos[1])
                elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
                    self.dragging_right = False
                elif event.type == pygame.MOUSEMOTION and self.dragging_right:
                    pos = getattr(event, "pos", pygame.mouse.get_pos())
                    self.right_center = (
                        max(self.play_area.left + 40, min(self.play_area.right - 40, pos[0] + self.drag_offset[0])),
                        max(self.play_area.top + 40, min(self.play_area.bottom - 40, pos[1] + self.drag_offset[1])),
                    )

            else:
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_RETURN:
                        self.state = self.STATE_HOME
                    elif event.key == pygame.K_ESCAPE:
                        self._exit_to_main_menu()
                elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    pos = getattr(event, "pos", pygame.mouse.get_pos())
                    if self.btn_continue.collidepoint(pos):
                        self.state = self.STATE_HOME
                    elif self.btn_exit.collidepoint(pos):
                        self._exit_to_main_menu()

    def update(self):
        now = time.time()
        if self.state == self.STATE_PLAY:
            self.session_elapsed, self.attempt_elapsed = self.session.tick(now)
            if self.session.is_session_complete():
                self._finish_game()
                return
            if self.session.is_attempt_timed_out():
                self.scoring.on_failure()
                self._set_feedback("eye_find.fail", (238, 118, 118))
                self.session.restart_attempt(now)
        if self.feedback_text and now > self.feedback_until:
            self.feedback_text = ""

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
        step = self.small_font.render(f"{idx}. {text}", True, (58, 84, 118))
        screen.blit(step, (x + 52, y + 6))

    def _draw_home(self, screen):
        title = self.title_font.render(self.manager.t("eye_find.title"), True, (38, 66, 108))
        screen.blit(title, (self.width // 2 - title.get_width() // 2, 86))
        self._draw_button(screen, self.btn_naked, self.manager.t("eye_find.home.naked"), (64, 138, 212), icon_name="check")
        self._draw_button(screen, self.btn_glasses, self.manager.t("eye_find.home.glasses"), (90, 126, 222), icon_name="target")
        self._draw_button(screen, self.btn_help, self.manager.t("eye_find.home.help"), (126, 142, 174), icon_name="question")
        self._draw_button(screen, self.btn_back, self.manager.t("common.back"), (88, 116, 168), icon_name="back_arrow")

        if self.show_filter_picker:
            modal = pygame.Surface((self.filter_modal.width, self.filter_modal.height), pygame.SRCALPHA)
            modal.fill((248, 253, 255, 238))
            screen.blit(modal, self.filter_modal.topleft)
            pygame.draw.rect(screen, (116, 148, 196), self.filter_modal, 2, border_radius=12)
            msg = self.body_font.render(self.manager.t("eye_find.filter.pick"), True, (52, 76, 110))
            screen.blit(msg, (self.filter_modal.centerx - msg.get_width() // 2, self.filter_modal.y + 24))
            self._draw_filter_option(
                screen,
                self.filter_lr,
                self.manager.t("eye_find.filter.lr"),
                (255, 0, 0),
                (0, 0, 255),
                self.filter_direction == self.FILTER_LR,
            )
            self._draw_filter_option(
                screen,
                self.filter_rl,
                self.manager.t("eye_find.filter.rl"),
                (0, 0, 255),
                (255, 0, 0),
                self.filter_direction == self.FILTER_RL,
            )
            self._draw_button(screen, self.filter_start, self.manager.t("eye_find.filter.start"), (86, 150, 108), icon_name="check")

    def _draw_help(self, screen):
        title = self.title_font.render(self.manager.t("eye_find.help.title"), True, (42, 70, 110))
        deco = self.sub_font.render("?", True, (106, 136, 192))
        screen.blit(title, (self.width // 2 - title.get_width() // 2, 76))
        screen.blit(deco, (self.width // 2 + title.get_width() // 2 + 8, 86))
        screen.blit(deco, (self.width // 2 - title.get_width() // 2 - 22, 86))

        self._draw_help_step(screen, 1, 190, self.manager.t("eye_find.help.step1"))
        self._draw_help_step(screen, 2, 280, self.manager.t("eye_find.help.step2"))
        self._draw_help_step(screen, 3, 370, self.manager.t("eye_find.help.step3"))

        self._draw_button(screen, self.help_ok, self.manager.t("eye_find.help.ok"), (242, 214, 126), text_color=(104, 84, 42), icon_name="check")

    def _draw_play(self, screen):
        is_glasses_mode = self.mode == self.MODE_GLASSES
        hud_primary = (42, 12, 72) if is_glasses_mode else (55, 82, 122)
        hud_secondary = (88, 28, 92) if is_glasses_mode else (86, 104, 130)
        hud_alert = (132, 18, 32) if is_glasses_mode else (222, 74, 74)
        tip_color = (82, 22, 76) if is_glasses_mode else (106, 70, 70)
        direction_color = (32, 16, 112) if is_glasses_mode else (76, 96, 142)
        confirm_color = (52, 124, 82) if is_glasses_mode else (72, 148, 102)
        back_color = (62, 52, 128) if is_glasses_mode else (86, 116, 170)

        mode_text = self.manager.t("eye_find.mode.naked") if self.mode == self.MODE_NAKED else self.manager.t("eye_find.mode.glasses")
        mode_surface = self.body_font.render(mode_text, True, hud_primary)
        screen.blit(mode_surface, (24, 18))

        remaining = max(0, self._session_seconds() - self.session_elapsed)
        timer_color = hud_alert if remaining <= 30 else hud_primary
        timer_surface = self.body_font.render(self.manager.t("eye_find.time", sec=self._format_time(remaining)), True, timer_color)
        screen.blit(timer_surface, (self.width // 2 - timer_surface.get_width() // 2, 14))

        score_surface = self.body_font.render(self.manager.t("eye_find.score", score=self.scoring.score), True, hud_primary)
        screen.blit(score_surface, (self.width // 2 - score_surface.get_width() // 2, 44))

        if is_glasses_mode:
            glasses = self.small_font.render(self.manager.t("eye_find.glasses_tip"), True, tip_color)
            filter_text_key = "eye_find.filter.lr" if self.filter_direction == self.FILTER_LR else "eye_find.filter.rl"
            direction = self.small_font.render(self.manager.t(filter_text_key), True, direction_color)
            screen.blit(glasses, (24, 50))
            screen.blit(direction, (24, 74))

        left = self._apply_filter(self.pattern_surface, "left")
        right = self._apply_filter(self.pattern_surface, "right")
        blend_layer = self.pattern_service.blend_filtered_patterns(
            (self.width, self.height),
            left,
            left.get_rect(center=self.left_center),
            right,
            right.get_rect(center=self.right_center),
        )
        screen.blit(blend_layer, (0, 0))

        guide = self.small_font.render(self.manager.t("eye_find.play.guide"), True, hud_secondary)
        screen.blit(guide, (self.play_area.centerx - guide.get_width() // 2, self.play_area.bottom + 8))

        attempt_left = max(0, int(self.ATTEMPT_SECONDS - self.attempt_elapsed))
        attempt_color = hud_alert if attempt_left <= 8 else hud_secondary
        attempt_surface = self.small_font.render(self.manager.t("eye_find.attempt_time", sec=attempt_left), True, attempt_color)
        screen.blit(attempt_surface, (self.play_area.centerx - attempt_surface.get_width() // 2, self.play_area.bottom + 30))

        self._draw_button(screen, self.btn_confirm, self.manager.t("eye_find.confirm"), confirm_color, icon_name="check")
        self._draw_button(screen, self.btn_home, self.manager.t("common.back"), back_color, icon_name="back_arrow")

        if self.feedback_text:
            fb = self.body_font.render(self.feedback_text, True, self.feedback_color)
            screen.blit(fb, (self.width // 2 - fb.get_width() // 2, self.play_area.y - 36))

    def _draw_result(self, screen):
        title = self.title_font.render(self.manager.t("eye_find.result.title"), True, (42, 70, 110))
        screen.blit(title, (self.width // 2 - title.get_width() // 2, 100))

        mode_text = self.manager.t("eye_find.mode.naked") if self.final_stats.get("mode") == self.MODE_NAKED else self.manager.t("eye_find.mode.glasses")
        filter_text = "-"
        if self.final_stats.get("mode") == self.MODE_GLASSES:
            filter_text = self.manager.t(
                "eye_find.filter.lr" if self.final_stats.get("filter_direction") == self.FILTER_LR else "eye_find.filter.rl"
            )
        lines = [
            self.manager.t("eye_find.result.duration", sec=self.final_stats.get("duration", 0)),
            self.manager.t("eye_find.result.success", n=self.final_stats.get("success", 0)),
            self.manager.t("eye_find.result.score", n=self.final_stats.get("score", 0)),
            self.manager.t("eye_find.result.mode", mode=mode_text),
            self.manager.t("eye_find.result.filter", direction=filter_text),
            self.manager.t("eye_find.result.reset_tip"),
            self.manager.t("eye_find.result.eye_tip"),
        ]
        for idx, text in enumerate(lines):
            color = (58, 84, 118) if idx < 5 else (96, 114, 138)
            line = self.body_font.render(text, True, color)
            screen.blit(line, (self.width // 2 - line.get_width() // 2, 184 + idx * 36))

        self._draw_button(screen, self.btn_continue, self.manager.t("eye_find.result.continue"), (84, 148, 108), icon_name="check")
        self._draw_button(screen, self.btn_exit, self.manager.t("eye_find.result.exit"), (120, 134, 168), icon_name="cross")

    def draw(self, screen):
        self.refresh_fonts_if_needed()
        self._draw_gradient_bg(screen)
        if self.state == self.STATE_HOME:
            self._draw_home(screen)
        elif self.state == self.STATE_HELP:
            self._draw_help(screen)
        elif self.state == self.STATE_PLAY:
            self._draw_play(screen)
        else:
            self._draw_result(screen)
