import time
from datetime import datetime

import pygame

from core.base_scene import BaseScene
from games.common.anaglyph import (
    FILTER_LR,
    FILTER_RL,
    BLUE_FILTER,
    GLASSES_BACKGROUND,
    RED_FILTER,
)

from ..services import TangramFusionBoardService, TangramFusionScoringService, TangramFusionSessionService


class TangramFusionScene(BaseScene):
    STATE_HOME = "home"
    STATE_HELP = "help"
    STATE_PLAY = "play"
    STATE_RESULT = "result"
    MODE_GLASSES = "glasses"
    HOME_VERTICAL_UNIT = 14

    def __init__(self, manager):
        super().__init__(manager)
        self.width = 900
        self.height = 700
        self.state = self.STATE_HOME
        self.mode = self.MODE_GLASSES
        self.filter_direction = FILTER_LR
        self.show_filter_picker = False
        self.feedback_text = ""
        self.feedback_color = (255, 255, 255)
        self.feedback_until = 0.0
        self.final_stats = {}
        self.round_index = 0
        self.selected_option = 0
        self.round_started_at = 0.0
        self.pending_next_round_at = 0.0
        self.pending_correct_option = None
        self.board_service = TangramFusionBoardService()
        self.scoring = TangramFusionScoringService()
        self.session = TangramFusionSessionService(self._session_seconds())
        self.round_data = {}
        self._refresh_fonts()
        self._build_ui()

    def _refresh_fonts(self):
        self.title_font = self.create_font(52)
        self.sub_font = self.create_font(26)
        self.option_font = self.create_font(28)
        self.body_font = self.create_font(22)
        self.small_font = self.create_font(18)

    def _build_ui(self):
        card_w = min(560, self.width - 120)
        start_x = self.width // 2 - card_w // 2
        choice_gap = 16
        choice_w = (card_w - choice_gap) // 2
        button_y = 232 + self.HOME_VERTICAL_UNIT * 3
        self.btn_start = pygame.Rect(start_x, button_y, choice_w, 58)
        self.filter_lr = self.btn_start.copy()
        self.filter_rl = pygame.Rect(self.btn_start.right + choice_gap, button_y, choice_w, 58)
        self.btn_help = pygame.Rect(start_x, button_y + 74, card_w, 58)
        self.btn_back = pygame.Rect(self.width - 110, 18, 88, 36)
        self.btn_home = pygame.Rect(self.width - 110, 18, 88, 36)
        self.btn_continue = pygame.Rect(self.width // 2 - 210, self.height - 100, 180, 48)
        self.btn_exit = pygame.Rect(self.width // 2 + 30, self.height - 100, 180, 48)
        self.help_ok = pygame.Rect(self.width // 2 - 90, self.height - 90, 180, 54)
        self.filter_modal = pygame.Rect(self.width // 2 - 250, self.height // 2 - 128, 500, 220)
        self.filter_start = pygame.Rect(self.filter_modal.centerx - 90, self.filter_modal.y + 150, 180, 44)
        self.target_rect = pygame.Rect(self.width // 2 - 260, 144, 520, 280)
        option_y = self.height - 156
        self.option_rects = [
            pygame.Rect(self.width // 2 - 258, option_y, 156, 72),
            pygame.Rect(self.width // 2 - 78, option_y, 156, 72),
            pygame.Rect(self.width // 2 + 102, option_y, 156, 72),
        ]

    def on_resize(self, width, height):
        self.width = width
        self.height = height
        self._build_ui()

    def reset(self):
        self.state = self.STATE_HOME
        self.mode = self.MODE_GLASSES
        self.filter_direction = FILTER_LR
        self.show_filter_picker = False
        self.feedback_text = ""
        self.feedback_color = (255, 255, 255)
        self.feedback_until = 0.0
        self.final_stats = {}
        self.round_index = 0
        self.selected_option = 0
        self.round_started_at = 0.0
        self.pending_next_round_at = 0.0
        self.pending_correct_option = None
        self.scoring.reset()
        self.session.session_seconds = self._session_seconds()
        self.session.reset()
        self.round_data = {}

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
        if text:
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
        if self.state == self.STATE_PLAY:
            screen.fill(GLASSES_BACKGROUND[:3])
            return
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

    def _start_game(self):
        self.state = self.STATE_PLAY
        self.scoring.reset()
        self.session.session_seconds = self._session_seconds()
        self.session.start()
        self.round_index = 0
        self.pending_next_round_at = 0.0
        self.pending_correct_option = None
        self._new_round()
        self._set_feedback("tangram_fusion.feedback.start", (122, 170, 228))

    def _new_round(self):
        self.round_data = self.board_service.create_round(self._stage_index(), self.filter_direction)
        self.selected_option = 0
        self.round_started_at = time.time()
        self.round_index += 1

    def _set_feedback(self, key, color):
        self.feedback_text = self.manager.t(key)
        self.feedback_color = color
        self.feedback_until = time.time() + 0.9

    def _answer(self, option_index):
        if self.pending_next_round_at:
            return
        response_time = time.time() - self.round_started_at
        correct = option_index == self.round_data["correct_option"]
        self.scoring.on_answer(correct, response_time, self.round_data["stage_index"])
        if correct:
            self.pending_correct_option = option_index
            self.pending_next_round_at = time.time() + 0.42
            self._set_feedback("tangram_fusion.feedback.correct", (96, 176, 116))
            self.play_correct_sound()
        else:
            self._set_feedback("tangram_fusion.feedback.wrong", (214, 96, 96))
            self.play_wrong_sound()

    def _save_result(self):
        data_manager = getattr(self.manager, "data_manager", None)
        if not data_manager:
            return
        data_manager.save_training_session(
            {
                "timestamp": datetime.now().isoformat(),
                "game_id": "fusion.tangram_fusion",
                "difficulty_level": 3,
                "total_questions": self.scoring.success_count + self.scoring.failure_count,
                "correct_count": self.scoring.success_count,
                "wrong_count": self.scoring.failure_count,
                "duration_seconds": float(self.final_stats.get("duration", 0)),
                "accuracy_rate": self.final_stats.get("accuracy", 0.0),
                "training_metrics": {
                    "tangram_completion_accuracy": self.final_stats.get("accuracy", 0.0),
                    "avg_solve_time": self.final_stats.get("avg_select_time", 0.0),
                    "best_streak": self.final_stats.get("best_streak", 0),
                    "completed_shapes": self.final_stats.get("success", 0),
                },
            }
        )

    def _finish_game(self):
        self.final_stats = {
            "duration": int(self.session.session_elapsed),
            "success": self.scoring.completed_shapes,
            "wrong": self.scoring.failure_count,
            "accuracy": self.scoring.accuracy(),
            "score": self.scoring.score,
            "best_streak": self.scoring.best_streak,
            "avg_select_time": self.scoring.average_select_time(),
            "filter_direction": self.filter_direction,
        }
        self.state = self.STATE_RESULT
        self.play_completed_sound()
        self._save_result()

    def _draw_filter_picker(self, screen):
        for rect, text, left, right, selected in (
            (self.filter_lr, self.manager.t("tangram_fusion.filter.lr"), RED_FILTER[:3], BLUE_FILTER[:3], self.filter_direction == FILTER_LR),
            (self.filter_rl, self.manager.t("tangram_fusion.filter.rl"), BLUE_FILTER[:3], RED_FILTER[:3], self.filter_direction == FILTER_RL),
        ):
            self._draw_button(screen, rect, "", (244, 247, 255), text_color=(62, 72, 98), selected=selected)
            preview_rect = pygame.Rect(rect.x + 16, rect.y + 10, 56, rect.height - 20)
            pygame.draw.rect(screen, left, pygame.Rect(preview_rect.x, preview_rect.y, preview_rect.width // 2, preview_rect.height), border_top_left_radius=8, border_bottom_left_radius=8)
            pygame.draw.rect(screen, right, pygame.Rect(preview_rect.centerx, preview_rect.y, preview_rect.width // 2, preview_rect.height), border_top_right_radius=8, border_bottom_right_radius=8)
            pygame.draw.rect(screen, (255, 255, 255) if selected else (190, 206, 228), preview_rect, 2, border_radius=8)
            label = self.small_font.render(text, True, (62, 72, 98))
            screen.blit(label, (preview_rect.right + 16, rect.centery - label.get_height() // 2))

    def _fit_polygon(self, polygon, rect):
        xs = [point[0] for point in polygon]
        ys = [point[1] for point in polygon]
        min_x, max_x = min(xs), max(xs)
        min_y, max_y = min(ys), max(ys)
        width = max(1, max_x - min_x)
        height = max(1, max_y - min_y)
        scale = min((rect.width - 18) / width, (rect.height - 18) / height)
        offset_x = rect.x + (rect.width - width * scale) / 2 - min_x * scale
        offset_y = rect.y + (rect.height - height * scale) / 2 - min_y * scale
        return [(int(offset_x + x * scale), int(offset_y + y * scale)) for x, y in polygon]

    def _template_points(self, template):
        source = []
        for slot in template["slots"]:
            source.extend(slot["polygon"])
        return source

    def _fit_board_polygon(self, polygon, board_rect, template):
        source = self._template_points(template)
        xs = [point[0] for point in source]
        ys = [point[1] for point in source]
        min_x, max_x = min(xs), max(xs)
        min_y, max_y = min(ys), max(ys)
        width = max(1, max_x - min_x)
        height = max(1, max_y - min_y)
        inset_rect = board_rect.inflate(-54, -44)
        scale = min(inset_rect.width / width, inset_rect.height / height)
        offset_x = inset_rect.x + (inset_rect.width - width * scale) / 2 - min_x * scale
        offset_y = inset_rect.y + (inset_rect.height - height * scale) / 2 - min_y * scale
        return [(int(offset_x + x * scale), int(offset_y + y * scale)) for x, y in polygon]

    def _board_scaled_polygon(self, polygon, template):
        board_points = self._fit_board_polygon(polygon, self.target_rect, template)
        return [(x - self.target_rect.x, y - self.target_rect.y) for x, y in board_points]

    def _translate_polygon_to_rect(self, polygon, rect):
        xs = [point[0] for point in polygon]
        ys = [point[1] for point in polygon]
        width = max(xs) - min(xs)
        height = max(ys) - min(ys)
        offset_x = rect.centerx - (min(xs) + width / 2)
        offset_y = rect.centery - (min(ys) + height / 2)
        return [(int(x + offset_x), int(y + offset_y)) for x, y in polygon]

    def _draw_piece_polygon(self, surface, polygon, color, outline=(255, 255, 255), outline_width=2):
        pygame.draw.polygon(surface, color, polygon)
        pygame.draw.polygon(surface, outline, polygon, outline_width)

    def _draw_hint_polygon(self, surface, polygon, alpha):
        pygame.draw.polygon(surface, (86, 94, 110, alpha), polygon)
        pygame.draw.polygon(surface, (255, 255, 255, max(28, alpha)), polygon, 2)

    def _missing_color(self):
        missing_side = self.round_data["slot_sides"][self.round_data["missing_index"]]
        return self.board_service.color_for_side(missing_side, self.filter_direction)

    def _draw_option_piece(self, screen, rect, option, selected=False):
        template = self.round_data["template"]
        polygon = self._translate_polygon_to_rect(self._board_scaled_polygon(option["polygon"], template), rect)
        if selected:
            glow = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
            pygame.draw.polygon(glow, (255, 230, 140, 64), polygon)
            screen.blit(glow, (0, 0))
        color = self._missing_color()
        outline = (255, 240, 184) if selected else (54, 68, 92)
        self._draw_piece_polygon(screen, polygon, color, outline=outline, outline_width=3 if selected else 2)

    def _draw_silhouette(self, surface, template):
        for slot in template["slots"]:
            polygon = self._board_scaled_polygon(slot["polygon"], template)
            pygame.draw.polygon(surface, (255, 255, 255, 46), polygon)
            pygame.draw.polygon(surface, (214, 224, 240, 96), polygon, 1)

    def _draw_target_board(self, screen):
        board = self.target_rect
        pygame.draw.rect(screen, GLASSES_BACKGROUND[:3], board, border_radius=18)
        pygame.draw.rect(screen, (255, 255, 255), board, 3, border_radius=18)
        template = self.round_data["template"]
        missing_index = self.round_data["missing_index"]
        board_size = board.size
        fill = pygame.Surface(board_size, pygame.SRCALPHA)
        hint = pygame.Surface(board_size, pygame.SRCALPHA)
        self._draw_silhouette(fill, template)
        for index, slot in enumerate(template["slots"]):
            if index == missing_index:
                self._draw_hint_polygon(hint, self._board_scaled_polygon(slot["polygon"], template), self.board_service.guide_alpha(self.round_data["stage_index"]))
            else:
                color = self.board_service.color_for_side(self.round_data["slot_sides"][index], self.filter_direction)
                self._draw_piece_polygon(fill, self._board_scaled_polygon(slot["polygon"], template), color)
        if self.pending_next_round_at and self.pending_correct_option == self.round_data["correct_option"]:
            color = self.board_service.color_for_side(self.round_data["slot_sides"][missing_index], self.filter_direction)
            self._draw_piece_polygon(fill, self._board_scaled_polygon(template["slots"][missing_index]["polygon"], template), color, outline=(255, 246, 196), outline_width=3)
        screen.blit(fill, board.topleft)
        screen.blit(hint, board.topleft)
        template_name = self.manager.t(f"tangram_fusion.template.{self.round_data['template_id']}")
        label = self.small_font.render(template_name, True, (255, 255, 255))
        screen.blit(label, (board.centerx - label.get_width() // 2, board.bottom + 10))

    def _draw_home(self, screen):
        title = self.title_font.render(self.manager.t("tangram_fusion.title"), True, (34, 60, 96))
        subtitle = self.sub_font.render(self.manager.t("tangram_fusion.subtitle"), True, (86, 104, 130))
        screen.blit(title, (self.width // 2 - title.get_width() // 2, 82))
        screen.blit(subtitle, (self.width // 2 - subtitle.get_width() // 2, 140))
        hint = self.body_font.render(self.manager.t("tangram_fusion.home.start"), True, (52, 76, 110))
        screen.blit(hint, (self.width // 2 - hint.get_width() // 2, 184 + self.HOME_VERTICAL_UNIT * 3))
        self._draw_filter_picker(screen)
        self._draw_button(screen, self.btn_help, self.manager.t("tangram_fusion.home.help"), (124, 140, 168))
        self._draw_button(screen, self.btn_back, self.manager.t("common.back"), (86, 116, 170))

    def _draw_help(self, screen):
        title = self.title_font.render(self.manager.t("tangram_fusion.help.title"), True, (34, 60, 96))
        screen.blit(title, (self.width // 2 - title.get_width() // 2, 76))
        for idx, key in enumerate(("tangram_fusion.help.step1", "tangram_fusion.help.step2", "tangram_fusion.help.step3")):
            card = pygame.Rect(90, 170 + idx * 104, self.width - 180, 88)
            pygame.draw.rect(screen, (246, 250, 255), card, border_radius=16)
            pygame.draw.rect(screen, (196, 212, 234), card, 2, border_radius=16)
            self._draw_wrapped_text(screen, f"{idx + 1}. {self.manager.t(key)}", card.x + 20, card.y + 16, card.width - 40)
        self._draw_button(screen, self.help_ok, self.manager.t("tangram_fusion.help.ok"), (244, 208, 120), text_color=(92, 76, 34))

    def _draw_play(self, screen):
        remaining = max(0, int(self.session.session_seconds - self.session.session_elapsed))
        hud = (78, 92, 114)
        timer = self.body_font.render(self.manager.t("tangram_fusion.time", sec=f"{remaining // 60:02d}:{remaining % 60:02d}"), True, hud)
        round_surface = self.small_font.render(self.manager.t("tangram_fusion.round", n=self.round_index), True, hud)
        goal = self.small_font.render(self.manager.t("tangram_fusion.goal"), True, hud)
        mode = self.small_font.render(self.manager.t("tangram_fusion.mode.glasses"), True, hud)
        progress = self.small_font.render(self.manager.t("tangram_fusion.progress", n=self.scoring.completed_shapes), True, hud)
        streak = self.small_font.render(self.manager.t("tangram_fusion.streak", n=self.scoring.current_streak), True, hud)
        stage = self.small_font.render(self.manager.t(self.board_service.stage_label_key(self.round_data["stage_index"])), True, hud)
        guide = self.small_font.render(self.manager.t("tangram_fusion.play.guide"), True, hud)
        tip = self.small_font.render(self.manager.t("tangram_fusion.play.tip"), True, hud)
        screen.blit(mode, (26, 18))
        screen.blit(progress, (26, 44))
        screen.blit(streak, (26, 70))
        screen.blit(timer, (self.width // 2 - timer.get_width() // 2, 14))
        screen.blit(round_surface, (self.width // 2 - round_surface.get_width() // 2, 48))
        screen.blit(goal, (self.width // 2 - goal.get_width() // 2, 72))
        self._draw_button(screen, self.btn_home, self.manager.t("common.back"), (86, 116, 170))
        screen.blit(stage, (self.target_rect.right - stage.get_width(), 18))
        screen.blit(guide, (self.width // 2 - guide.get_width() // 2, self.target_rect.y - 28))
        self._draw_target_board(screen)
        for index, rect in enumerate(self.option_rects):
            selected = index == self.selected_option
            self._draw_option_piece(screen, rect, self.round_data["options"][index], selected=selected)
        screen.blit(tip, (self.width // 2 - tip.get_width() // 2, self.option_rects[0].bottom + 12))
        if self.feedback_text and time.time() <= self.feedback_until:
            fb = self.body_font.render(self.feedback_text, True, self.feedback_color)
            screen.blit(fb, (self.width // 2 - fb.get_width() // 2, self.height - 36))

    def _draw_result(self, screen):
        title = self.title_font.render(self.manager.t("tangram_fusion.result.title"), True, (34, 60, 96))
        screen.blit(title, (self.width // 2 - title.get_width() // 2, 84))
        direction = self.manager.t(f"tangram_fusion.filter.value.{self.final_stats.get('filter_direction', FILTER_LR)}")
        lines = [
            self.manager.t("tangram_fusion.result.duration", sec=self.final_stats.get("duration", 0)),
            self.manager.t("tangram_fusion.result.success", n=self.final_stats.get("success", 0)),
            self.manager.t("tangram_fusion.result.wrong", n=self.final_stats.get("wrong", 0)),
            self.manager.t("tangram_fusion.result.accuracy", value=self.final_stats.get("accuracy", 0.0)),
            self.manager.t("tangram_fusion.result.score", n=self.final_stats.get("score", 0)),
            self.manager.t("tangram_fusion.result.streak", n=self.final_stats.get("best_streak", 0)),
            self.manager.t("tangram_fusion.result.avg_select_time", sec=self.final_stats.get("avg_select_time", 0.0)),
            self.manager.t("tangram_fusion.result.filter", direction=direction),
        ]
        for idx, text in enumerate(lines):
            line = self.body_font.render(text, True, (66, 84, 114))
            screen.blit(line, (self.width // 2 - line.get_width() // 2, 164 + idx * 34))
        self._draw_button(screen, self.btn_continue, self.manager.t("tangram_fusion.result.continue"), (84, 148, 108))
        self._draw_button(screen, self.btn_exit, self.manager.t("tangram_fusion.result.exit"), (120, 134, 168))

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
                continue
            if self.state == self.STATE_HOME:
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        self.manager.set_scene("category")
                    elif event.key in (pygame.K_LEFT, pygame.K_UP):
                        self.filter_direction = FILTER_LR
                    elif event.key in (pygame.K_RIGHT, pygame.K_DOWN):
                        self.filter_direction = FILTER_RL
                    elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
                        self._start_game()
                    elif event.key == pygame.K_h:
                        self.state = self.STATE_HELP
                elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    pos = getattr(event, "pos", pygame.mouse.get_pos())
                    if self.btn_back.collidepoint(pos):
                        self.manager.set_scene("category")
                    elif self.filter_lr.collidepoint(pos):
                        self.filter_direction = FILTER_LR
                        self._start_game()
                    elif self.filter_rl.collidepoint(pos):
                        self.filter_direction = FILTER_RL
                        self._start_game()
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
                        self.manager.set_scene("menu")
                    elif self.pending_next_round_at:
                        continue
                    elif event.key in (pygame.K_LEFT, pygame.K_UP):
                        self.selected_option = (self.selected_option - 1) % len(self.option_rects)
                    elif event.key in (pygame.K_RIGHT, pygame.K_DOWN):
                        self.selected_option = (self.selected_option + 1) % len(self.option_rects)
                    elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
                        self._answer(self.selected_option)
                elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    pos = getattr(event, "pos", pygame.mouse.get_pos())
                    if self.btn_home.collidepoint(pos):
                        self.manager.set_scene("menu")
                    elif not self.pending_next_round_at:
                        for index, rect in enumerate(self.option_rects):
                            if rect.collidepoint(pos):
                                self.selected_option = index
                                self._answer(index)
                                break
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
        if self.state != self.STATE_PLAY:
            return
        self.session.tick()
        now = time.time()
        if self.pending_next_round_at and now >= self.pending_next_round_at:
            self.pending_next_round_at = 0.0
            self.pending_correct_option = None
            self._new_round()
        if self.session.is_complete():
            self._finish_game()

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
