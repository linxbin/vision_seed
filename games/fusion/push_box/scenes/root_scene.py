import time
from datetime import datetime

import pygame

from core.asset_loader import load_image_if_exists, project_path
from core.base_scene import BaseScene
from games.common.anaglyph import (
    BLUE_FILTER,
    FILTER_LR,
    FILTER_RL,
    GLASSES_BACKGROUND,
    GLASSES_BUTTON_COLOR,
    MODE_GLASSES,
    RED_FILTER,
    apply_filter,
)

from ..services import FusionPushBoxBoardService, FusionPushBoxScoringService, FusionPushBoxSessionService


class FusionPushBoxScene(BaseScene):
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
        self.feedback_text = ""
        self.feedback_color = (255, 255, 255)
        self.feedback_until = 0.0
        self.restart_pending_until = 0.0
        self.final_stats = {}
        self.level_index = 0
        self.board_service = FusionPushBoxBoardService()
        self.scoring = FusionPushBoxScoringService()
        self.session = FusionPushBoxSessionService(self._session_seconds())
        self.board_state = self.board_service.create_level(0)
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
        board_w = min(self.width - 150, 760)
        board_h = min(self.height - 250, 520)
        self.board_rect = pygame.Rect(self.width // 2 - board_w // 2, 132, board_w, board_h)

    def on_resize(self, width, height):
        self.width = width
        self.height = height
        self._build_ui()

    def reset(self):
        self.state = self.STATE_HOME
        self.mode = self.MODE_NAKED
        self.filter_direction = self.FILTER_LR
        self.show_filter_picker = False
        self.feedback_text = ""
        self.restart_pending_until = 0.0
        self.final_stats = {}
        self.scoring.reset()
        self.session.session_seconds = self._session_seconds()
        self.session.reset()
        self.level_index = 0
        self.board_state = self.board_service.create_level(0)

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

    def _set_feedback(self, key, color):
        self.feedback_text = self.manager.t(key)
        self.feedback_color = color
        self.feedback_until = time.time() + 1.0

    def _play_sound(self, method_name):
        sound_manager = getattr(self.manager, "sound_manager", None)
        if not sound_manager:
            return
        method = getattr(sound_manager, method_name, None)
        if method:
            method()

    def _start_game(self):
        self.state = self.STATE_PLAY
        self.scoring.reset()
        self.session.session_seconds = self._session_seconds()
        self.session.start()
        self.level_index = 0
        self.board_state = self.board_service.create_level(0)
        self.restart_pending_until = 0.0
        self._set_feedback("fusion_push_box.feedback.start", (116, 162, 228))

    def _load_next_level(self):
        self.level_index += 1
        self.board_state = self.board_service.create_level(self.level_index)

    def _reset_level(self):
        self.board_state = self.board_service.create_level(self.level_index)
        self.restart_pending_until = 0.0
        self._set_feedback("fusion_push_box.feedback.reset", (130, 152, 196))
        self._play_sound("play_wrong")

    def _fail_and_restart_level(self):
        self.scoring.current_streak = 0
        self._set_feedback("fusion_push_box.feedback.deadlock", (236, 132, 132))
        self.restart_pending_until = time.time() + 1.0
        self._play_sound("play_wrong")

    def _finish_game(self):
        self.state = self.STATE_RESULT
        duration = int(self.session.session_elapsed)
        self.final_stats = {
            "duration": duration,
            "score": self.scoring.score,
            "clear_count": self.scoring.clear_count,
            "steps": self.scoring.total_steps,
            "mode": self.mode,
            "filter_direction": self.filter_direction,
            "encouragement": self._result_encouragement(),
        }
        self._play_sound("play_completed")
        self._save_result()

    def _result_encouragement(self):
        if self.scoring.clear_count >= 3:
            return self.manager.t("fusion_push_box.result.encourage.clear")
        return self.manager.t("fusion_push_box.result.encourage.keep")

    def _save_result(self):
        data_manager = getattr(self.manager, "data_manager", None)
        if not data_manager:
            return
        payload = {
            "timestamp": datetime.now().isoformat(),
            "game_id": "fusion.push_box",
            "difficulty_level": 3,
            "total_questions": max(1, self.scoring.clear_count),
            "correct_count": self.scoring.clear_count,
            "wrong_count": 0,
            "duration_seconds": float(self.final_stats.get("duration", 0)),
            "accuracy_rate": 100.0 if self.scoring.clear_count > 0 else 0.0,
            "training_metrics": {
                "fusion_clear_count": self.scoring.clear_count,
                "total_steps": self.scoring.total_steps,
                "total_pushes": self.scoring.total_pushes,
                "best_streak": self.scoring.best_streak,
            },
        }
        data_manager.save_training_session(payload)

    def _go_category(self):
        self.manager.set_scene("category")

    def _go_menu(self):
        self.manager.set_scene("menu")

    def _attempt_move(self, direction):
        moved, pushed = self.board_service.attempt_move(self.board_state, direction)
        if not moved:
            self.scoring.current_streak = 0
            self._set_feedback("fusion_push_box.feedback.blocked", (232, 126, 126))
            self._play_sound("play_wrong")
            return
        self.scoring.register_step(pushed)
        if pushed:
            self._set_feedback("fusion_push_box.feedback.push", (122, 206, 146))
            self._play_sound("play_correct")
        if self.board_service.is_cleared(self.board_state):
            self.scoring.on_clear(self.board_state["steps"], self.board_state["pushes"])
            self._set_feedback("fusion_push_box.feedback.clear", (255, 210, 120))
            self._play_sound("play_completed")
            self._load_next_level()
            return
        if not self.board_service.is_state_solvable(self.board_state):
            self._fail_and_restart_level()
            return
        if not self.board_service.has_any_pushable_box(self.board_state):
            self._fail_and_restart_level()

    def _draw_background(self, screen):
        top = (230, 243, 255)
        bottom = (215, 236, 252)
        overlay = None
        if self.state == self.STATE_PLAY and self.mode == self.MODE_GLASSES:
            overlay = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
            overlay.fill(GLASSES_BACKGROUND)
        for y in range(self.height):
            t = y / max(1, self.height - 1)
            color = (
                int(top[0] * (1 - t) + bottom[0] * t),
                int(top[1] * (1 - t) + bottom[1] * t),
                int(top[2] * (1 - t) + bottom[2] * t),
            )
            pygame.draw.line(screen, color, (0, y), (self.width, y))
        if overlay is not None:
            screen.blit(overlay, (0, 0))

    def _grid_metrics(self):
        cell = min(
            self.board_rect.width // self.board_state["width"],
            self.board_rect.height // self.board_state["height"],
        )
        grid_w = cell * self.board_state["width"]
        grid_h = cell * self.board_state["height"]
        offset_x = (self.board_rect.width - grid_w) // 2
        offset_y = (self.board_rect.height - grid_h) // 2
        return cell, offset_x, offset_y

    def _draw_board_base(self, surface):
        surface.fill((0, 0, 0, 0))
        cell, offset_x, offset_y = self._grid_metrics()
        for y in range(self.board_state["height"]):
            for x in range(self.board_state["width"]):
                rect = pygame.Rect(offset_x + x * cell, offset_y + y * cell, cell, cell).inflate(-6, -6)
                if (x, y) in self.board_state["walls"]:
                    pygame.draw.rect(surface, (124, 145, 182), rect, border_radius=12)
                else:
                    pygame.draw.rect(surface, (244, 248, 255), rect, border_radius=10)
                if (x, y) in self.board_state["targets"]:
                    center = rect.center
                    pygame.draw.circle(surface, (255, 226, 124), center, max(7, cell // 7))
                    pygame.draw.circle(surface, (255, 245, 202), center, max(3, cell // 11))

    def _draw_entities(self, surface, show_player, show_boxes):
        surface.fill((0, 0, 0, 0))
        cell, offset_x, offset_y = self._grid_metrics()
        if show_boxes:
            for box in self.board_state["boxes"]:
                rect = pygame.Rect(offset_x + box[0] * cell, offset_y + box[1] * cell, cell, cell).inflate(-18, -18)
                color = (248, 184, 82)
                pygame.draw.rect(surface, color, rect, border_radius=10)
                pygame.draw.rect(surface, (135, 92, 48), rect, 3, border_radius=10)
        if show_player:
            px, py = self.board_state["player"]
            center = (offset_x + px * cell + cell // 2, offset_y + py * cell + cell // 2)
            color = (82, 160, 255)
            pygame.draw.circle(surface, color, center, max(10, cell // 4))
            pygame.draw.circle(surface, (255, 255, 255), (center[0] - 6, center[1] - 4), 3)
            pygame.draw.circle(surface, (255, 255, 255), (center[0] + 6, center[1] - 4), 3)

    def _draw_play_board(self, screen):
        board_size = self.board_rect.size
        base = pygame.Surface(board_size, pygame.SRCALPHA)
        self._draw_board_base(base)
        screen.blit(base, self.board_rect.topleft)
        left_layer = pygame.Surface(board_size, pygame.SRCALPHA)
        right_layer = pygame.Surface(board_size, pygame.SRCALPHA)
        if self.mode == self.MODE_GLASSES:
            player_on_left = self.filter_direction == self.FILTER_LR
            self._draw_entities(
                left_layer,
                show_player=player_on_left,
                show_boxes=not player_on_left,
            )
            self._draw_entities(
                right_layer,
                show_player=not player_on_left,
                show_boxes=player_on_left,
            )
            left_layer = apply_filter(left_layer, self.mode, self.filter_direction, "left")
            right_layer = apply_filter(right_layer, self.mode, self.filter_direction, "right")
            screen.blit(left_layer, self.board_rect.topleft)
            screen.blit(right_layer, self.board_rect.topleft)
        else:
            combined = pygame.Surface(board_size, pygame.SRCALPHA)
            self._draw_entities(combined, show_player=True, show_boxes=True)
            screen.blit(combined, self.board_rect.topleft)

    def handle_events(self, events):
        for event in events:
            if self.state == self.STATE_HOME:
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        self._go_category()
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
                        self._go_category()
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
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        self._go_menu()
                    elif self.restart_pending_until and time.time() < self.restart_pending_until:
                        continue
                    elif event.key == pygame.K_r:
                        self._reset_level()
                    elif event.key == pygame.K_UP:
                        self._attempt_move("up")
                    elif event.key == pygame.K_DOWN:
                        self._attempt_move("down")
                    elif event.key == pygame.K_LEFT:
                        self._attempt_move("left")
                    elif event.key == pygame.K_RIGHT:
                        self._attempt_move("right")
                elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    pos = getattr(event, "pos", pygame.mouse.get_pos())
                    if self.btn_home.collidepoint(pos):
                        self._go_menu()
            else:
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_RETURN:
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
        if self.state != self.STATE_PLAY:
            return
        if self.restart_pending_until:
            if time.time() >= self.restart_pending_until:
                self.board_state = self.board_service.create_level(self.level_index)
                self.restart_pending_until = 0.0
            else:
                return
        self.session.tick()
        if self.session.is_complete():
            self._finish_game()

    def draw(self, screen):
        self.refresh_fonts_if_needed()
        self._draw_background(screen)
        if self.state == self.STATE_HOME:
            title = self.title_font.render(self.manager.t("fusion_push_box.title"), True, (43, 61, 93))
            subtitle = self.sub_font.render(self.manager.t("fusion_push_box.subtitle"), True, (97, 118, 148))
            screen.blit(title, (self.width // 2 - title.get_width() // 2, 92))
            screen.blit(subtitle, (self.width // 2 - subtitle.get_width() // 2, 144))
            self._draw_button(screen, self.btn_naked, self.manager.t("fusion_push_box.home.naked"), (72, 130, 214), icon_name="target")
            self._draw_button(
                screen,
                self.btn_glasses,
                self.manager.t("fusion_push_box.home.glasses"),
                GLASSES_BUTTON_COLOR,
                icon_name="star",
            )
            self._draw_button(screen, self.btn_help, self.manager.t("fusion_push_box.home.help"), (92, 116, 148), icon_name="question")
            self._draw_button(screen, self.btn_back, self.manager.t("common.back"), (92, 116, 148), icon_name="back_arrow")
            if self.show_filter_picker:
                pygame.draw.rect(screen, (255, 255, 255), self.filter_modal, border_radius=18)
                pygame.draw.rect(screen, (184, 205, 236), self.filter_modal, 2, border_radius=18)
                title = self.option_font.render(self.manager.t("fusion_push_box.filter.pick"), True, (50, 65, 96))
                screen.blit(title, (self.filter_modal.centerx - title.get_width() // 2, self.filter_modal.y + 20))
                self._draw_filter_option(
                    screen,
                    self.filter_lr,
                    self.manager.t("fusion_push_box.filter.lr"),
                    RED_FILTER[:3],
                    BLUE_FILTER[:3],
                    self.filter_direction == self.FILTER_LR,
                )
                self._draw_filter_option(
                    screen,
                    self.filter_rl,
                    self.manager.t("fusion_push_box.filter.rl"),
                    BLUE_FILTER[:3],
                    RED_FILTER[:3],
                    self.filter_direction == self.FILTER_RL,
                )
                self._draw_button(screen, self.filter_start, self.manager.t("fusion_push_box.filter.start"), (63, 154, 92), icon_name="check")
            return
        if self.state == self.STATE_HELP:
            panel = pygame.Rect(80, 100, self.width - 160, self.height - 180)
            pygame.draw.rect(screen, (255, 255, 255), panel, border_radius=18)
            pygame.draw.rect(screen, (184, 205, 236), panel, 2, border_radius=18)
            title = self.title_font.render(self.manager.t("fusion_push_box.help.title"), True, (43, 61, 93))
            screen.blit(title, (self.width // 2 - title.get_width() // 2, panel.y + 30))
            tips = (
                self.manager.t("fusion_push_box.help.step1"),
                self.manager.t("fusion_push_box.help.step2"),
                self.manager.t("fusion_push_box.help.step3"),
            )
            for index, tip in enumerate(tips, start=1):
                line = self.body_font.render(f"{index}. {tip}", True, (74, 92, 124))
                screen.blit(line, (panel.x + 42, panel.y + 120 + (index - 1) * 64))
            self._draw_button(screen, self.help_ok, self.manager.t("fusion_push_box.help.ok"), (63, 154, 92), icon_name="check")
            return
        if self.state == self.STATE_PLAY:
            score = self.small_font.render(self.manager.t("fusion_push_box.score", score=self.scoring.score), True, (43, 61, 93))
            left = max(0, int(self.session.session_seconds - self.session.session_elapsed))
            time_surface = self.small_font.render(self.manager.t("fusion_push_box.time", sec=left), True, (43, 61, 93))
            level_surface = self.small_font.render(self.manager.t("fusion_push_box.level", index=self.level_index + 1), True, (43, 61, 93))
            screen.blit(score, (36, 24))
            screen.blit(time_surface, (36, 54))
            screen.blit(level_surface, (36, 84))
            self._draw_button(screen, self.btn_home, self.manager.t("common.back"), (92, 116, 148), icon_name="home")
            self._draw_play_board(screen)
            guide = self.small_font.render(self.manager.t("fusion_push_box.play.guide"), True, (96, 114, 142))
            legend = self.small_font.render(self.manager.t("fusion_push_box.play.legend"), True, (96, 114, 142))
            screen.blit(guide, (self.width // 2 - guide.get_width() // 2, self.board_rect.bottom + 18))
            screen.blit(legend, (self.width // 2 - legend.get_width() // 2, self.board_rect.bottom + 42))
            if self.feedback_text and time.time() <= self.feedback_until:
                feedback = self.body_font.render(self.feedback_text, True, self.feedback_color)
                screen.blit(feedback, (self.width // 2 - feedback.get_width() // 2, self.height - 46))
            if self.restart_pending_until and time.time() < self.restart_pending_until:
                self._draw_failure_overlay(screen)
            return
        panel = pygame.Rect(90, 88, self.width - 180, self.height - 170)
        pygame.draw.rect(screen, (255, 255, 255), panel, border_radius=18)
        pygame.draw.rect(screen, (184, 205, 236), panel, 2, border_radius=18)
        title = self.title_font.render(self.manager.t("fusion_push_box.result.title"), True, (43, 61, 93))
        screen.blit(title, (self.width // 2 - title.get_width() // 2, panel.y + 28))
        lines = (
            self.manager.t("fusion_push_box.result.duration", sec=self.final_stats.get("duration", 0)),
            self.manager.t("fusion_push_box.result.cleared", n=self.final_stats.get("clear_count", 0)),
            self.manager.t("fusion_push_box.result.score", n=self.final_stats.get("score", 0)),
            self.manager.t("fusion_push_box.result.steps", n=self.final_stats.get("steps", 0)),
            self.manager.t(
                "fusion_push_box.result.mode",
                mode=self.manager.t(
                    "fusion_push_box.mode.glasses" if self.final_stats.get("mode") == self.MODE_GLASSES else "fusion_push_box.mode.naked"
                ),
            ),
            self.manager.t("fusion_push_box.result.filter", direction=self.final_stats.get("filter_direction", self.FILTER_LR)),
            self.final_stats.get("encouragement", ""),
        )
        for index, line in enumerate(lines):
            surface = self.body_font.render(line, True, (72, 90, 122))
            screen.blit(surface, (panel.x + 48, panel.y + 118 + index * 44))
        self._draw_button(screen, self.btn_continue, self.manager.t("fusion_push_box.result.continue"), (63, 154, 92), icon_name="check")
        self._draw_button(screen, self.btn_exit, self.manager.t("fusion_push_box.result.exit"), (92, 116, 148), icon_name="power")

    def _draw_failure_overlay(self, screen):
        overlay = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        overlay.fill((34, 28, 40, 118))
        screen.blit(overlay, (0, 0))
        panel = pygame.Rect(self.width // 2 - 230, self.height // 2 - 86, 460, 172)
        pygame.draw.rect(screen, (255, 248, 248), panel, border_radius=20)
        pygame.draw.rect(screen, (232, 150, 150), panel, 3, border_radius=20)
        title = self.option_font.render(self.manager.t("fusion_push_box.overlay.fail_title"), True, (126, 58, 58))
        body = self.body_font.render(self.manager.t("fusion_push_box.overlay.fail_body"), True, (108, 82, 82))
        screen.blit(title, (panel.centerx - title.get_width() // 2, panel.y + 34))
        screen.blit(body, (panel.centerx - body.get_width() // 2, panel.y + 82))
