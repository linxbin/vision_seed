import time
from datetime import datetime

import pygame

from core.base_scene import BaseScene
from games.common.anaglyph import (
    FILTER_LR,
    FILTER_RL,
    GLASSES_BUTTON_COLOR,
    MODE_GLASSES,
    RED_FILTER,
    BLUE_FILTER,
    SUBTRACTIVE_BACKGROUND,
    apply_filter,
    blend_filtered_patterns,
)

from ..services import RingFlightBoardService, RingFlightScoringService, RingFlightSessionService


class RingFlightScene(BaseScene):
    STATE_HOME = "home"
    STATE_HELP = "help"
    STATE_PLAY = "play"
    STATE_RESULT = "result"
    MODE_GLASSES = MODE_GLASSES
    TARGET_DEPTH_SEQUENCE = (0, 1, 2)
    RING_SPEED = 0.0135
    SELECT_PROGRESS = 0.62
    PLANE_DISPARITY = 18
    FLY_THROUGH_DURATION = 0.32
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
        self.board_service = RingFlightBoardService()
        self.scoring = RingFlightScoringService()
        self.session = RingFlightSessionService(self._session_seconds())
        self.wave = {}
        self.awaiting_selection = False
        self.target_depth_index = 0
        self.plane_x = 0.0
        self.fly_through = None
        self._visual_phase = 0.0
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
        self.play_area = pygame.Rect(70, 136, self.width - 140, self.height - 238)
        self.plane_x = self.play_area.centerx

    def on_resize(self, width, height):
        self.width = width
        self.height = height
        self._build_ui()
        if self.state == self.STATE_PLAY:
            self._new_wave()

    def reset(self):
        self.state = self.STATE_HOME
        self.mode = self.MODE_GLASSES
        self.filter_direction = FILTER_LR
        self.show_filter_picker = False
        self.feedback_text = ""
        self.feedback_until = 0.0
        self.final_stats = {}
        self.scoring.reset()
        self.session.session_seconds = self._session_seconds()
        self.session.reset()
        self.wave = {}
        self.awaiting_selection = False
        self.target_depth_index = 0
        self.plane_x = self.play_area.centerx
        self.fly_through = None
        self._visual_phase = 0.0

    def _session_seconds(self):
        try:
            minutes = int(self.manager.settings.get("session_duration_minutes", 5))
        except (TypeError, ValueError):
            minutes = 5
        return max(60, minutes * 60)

    def _current_target_depth(self):
        return self.TARGET_DEPTH_SEQUENCE[self.target_depth_index]

    def _current_target_key(self):
        depth = self._current_target_depth()
        return f"ring_flight.target.{self.board_service.DEPTH_LABELS[depth]}"

    def _filter_direction_label(self, direction=None):
        direction = direction or self.filter_direction
        if direction == FILTER_RL:
            return self.manager.t("ring_flight.filter.rl")
        return self.manager.t("ring_flight.filter.lr")

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

    def _draw_filter_option(self, screen, rect, text, left_color, right_color, selected):
        self._draw_button(screen, rect, "", (244, 247, 255), text_color=(62, 72, 98), selected=selected)
        preview_rect = pygame.Rect(rect.x + 16, rect.y + 10, 56, rect.height - 20)
        left_rect = pygame.Rect(preview_rect.x, preview_rect.y, preview_rect.width // 2, preview_rect.height)
        right_rect = pygame.Rect(left_rect.right, preview_rect.y, preview_rect.width - left_rect.width, preview_rect.height)
        pygame.draw.rect(screen, left_color, left_rect, border_top_left_radius=8, border_bottom_left_radius=8)
        pygame.draw.rect(screen, right_color, right_rect, border_top_right_radius=8, border_bottom_right_radius=8)
        pygame.draw.rect(screen, (255, 255, 255), preview_rect, 2, border_radius=8)
        label = self.small_font.render(text, True, (62, 72, 98))
        screen.blit(label, (preview_rect.right + 16, rect.centery - label.get_height() // 2))

    def _draw_background(self, screen):
        if self.state == self.STATE_PLAY and self.mode == self.MODE_GLASSES:
            screen.fill(SUBTRACTIVE_BACKGROUND[:3])
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

    def _set_feedback(self, key, color):
        self.feedback_text = self.manager.t(key)
        self.feedback_color = color
        self.feedback_until = time.time() + 0.8

    def _new_wave(self):
        self.wave = self.board_service.create_wave(self.play_area)
        self.awaiting_selection = False
        self.fly_through = None

    def _start_game(self):
        self.state = self.STATE_PLAY
        self.scoring.reset()
        self.target_depth_index = 0
        self.plane_x = self.play_area.centerx
        self.session.session_seconds = self._session_seconds()
        self.session.start()
        self._new_wave()

    def _advance_target_if_needed(self):
        if not self.scoring.should_switch_target():
            return
        self.target_depth_index = (self.target_depth_index + 1) % len(self.TARGET_DEPTH_SEQUENCE)
        self.scoring.on_target_switch()

    def _selection_y(self):
        return self.play_area.top + 54 + self.SELECT_PROGRESS * (self.play_area.height - 134)

    def _plane_rect(self):
        rect = pygame.Rect(int(self.plane_x) - 30, self.play_area.bottom - 52, 60, 34)
        if self.fly_through:
            progress = min(1.0, max(0.0, (time.time() - self.fly_through["started_at"]) / self.fly_through["duration"]))
            base_y = self.play_area.bottom - 35
            if self.fly_through["result"] == "success":
                end_y = self._selection_y() - 10
                current_y = int(base_y + (end_y - base_y) * progress)
            else:
                current_y = int(base_y + (1.0 - abs(progress * 2.0 - 1.0)) * 20)
            rect.center = (self.fly_through["target_x"], current_y)
        return rect

    def _display_rings(self):
        return [self.board_service.ring_display_state(self.play_area, ring) for ring in self.wave.get("rings", [])]

    def _plane_target_index(self):
        displays = self._display_rings()
        if not displays:
            return None
        plane_center_x = self._plane_rect().centerx
        return min(range(len(displays)), key=lambda idx: abs(displays[idx]["center"][0] - plane_center_x))

    def _classify_wave_selection(self):
        target_depth = self._current_target_depth()
        plane_center_x = self._plane_rect().centerx
        matched_ring = None
        matched_display = None
        edge_hit = False
        displays = self._display_rings()
        for ring, display in zip(self.wave.get("rings", []), displays):
            delta = abs(plane_center_x - display["center"][0])
            if delta <= display["inner_radius"] * 0.62:
                matched_ring = ring
                matched_display = display
                break
            if delta <= display["radius"]:
                edge_hit = True
        if matched_ring:
            if matched_ring["depth"] == target_depth:
                return {"result": "success", "ring": matched_ring, "display": matched_display}
            return {"result": "wrong_depth", "ring": matched_ring, "display": matched_display}
        if edge_hit:
            return {"result": "edge", "ring": None, "display": None}
        return {"result": "miss", "ring": None, "display": None}

    def _finalize_wave_result(self, result):
        if result == "success":
            self.scoring.on_success()
            self.play_correct_sound()
            self._set_feedback("ring_flight.feedback.correct", (86, 174, 112))
            self._advance_target_if_needed()
            self._new_wave()
        elif result == "wrong_depth":
            self.scoring.on_failure("wrong_depth")
            self.play_wrong_sound()
            self._set_feedback("ring_flight.feedback.wrong_depth", (220, 132, 84))
            self.awaiting_selection = True
        elif result == "edge":
            self.scoring.on_failure("edge")
            self.play_wrong_sound()
            self._set_feedback("ring_flight.feedback.edge", (214, 108, 108))
            self.awaiting_selection = True
        else:
            self.scoring.on_failure("miss")
            self.play_wrong_sound()
            self._set_feedback("ring_flight.feedback.miss", (214, 96, 96))
            self.awaiting_selection = True

    def _start_fly_through(self):
        decision = self._classify_wave_selection()
        target_x = decision["display"]["center"][0] if decision["display"] else self._plane_rect().centerx
        self.awaiting_selection = False
        self.fly_through = {
            "started_at": time.time(),
            "duration": self.FLY_THROUGH_DURATION,
            "result": decision["result"],
            "target_x": int(target_x),
        }

    def _save_result(self):
        if getattr(self.manager, "data_manager", None):
            self.manager.data_manager.save_training_session(
                {
                    "timestamp": datetime.now().isoformat(),
                    "game_id": "stereopsis.ring_flight",
                    "difficulty_level": 3,
                    "total_questions": self.scoring.success_count + self.scoring.failure_count,
                    "correct_count": self.scoring.success_count,
                    "wrong_count": self.scoring.failure_count,
                    "duration_seconds": float(self.final_stats.get("duration", 0)),
                    "accuracy_rate": self.final_stats.get("accuracy", 0.0),
                    "training_metrics": {
                        "successful_passes": self.final_stats.get("success", 0),
                        "wrong_depth_count": self.final_stats.get("wrong_depth", 0),
                        "edge_hit_count": self.final_stats.get("edge", 0),
                        "target_switch_count": self.final_stats.get("switches", 0),
                    },
                }
            )

    def _finish_game(self):
        self.final_stats = {
            "duration": int(self.session.session_elapsed),
            "success": self.scoring.success_count,
            "wrong": self.scoring.failure_count,
            "accuracy": self.scoring.accuracy(),
            "score": self.scoring.score,
            "wrong_depth": self.scoring.wrong_depth_count,
            "edge": self.scoring.edge_hit_count,
            "switches": self.scoring.target_switch_count,
            "filter_direction": self.filter_direction,
        }
        self.state = self.STATE_RESULT
        self.play_completed_sound()
        self._save_result()

    def _draw_filter_picker(self, screen):
        overlay = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        overlay.fill((24, 32, 46, 136))
        screen.blit(overlay, (0, 0))
        pygame.draw.rect(screen, (249, 251, 255), self.filter_modal, border_radius=18)
        title = self.sub_font.render(self.manager.t("ring_flight.filter.pick"), True, (52, 70, 100))
        screen.blit(title, (self.filter_modal.centerx - title.get_width() // 2, self.filter_modal.y + 20))
        options = (
            (self.filter_lr, self.manager.t("ring_flight.filter.lr"), RED_FILTER[:3], BLUE_FILTER[:3], self.filter_direction == FILTER_LR),
            (self.filter_rl, self.manager.t("ring_flight.filter.rl"), BLUE_FILTER[:3], RED_FILTER[:3], self.filter_direction == FILTER_RL),
        )
        for rect, text, left, right, selected in options:
            self._draw_button(screen, rect, "", (244, 247, 255), text_color=(62, 72, 98), selected=selected)
            preview_rect = pygame.Rect(rect.x + 16, rect.y + 10, 56, rect.height - 20)
            pygame.draw.rect(screen, left, pygame.Rect(preview_rect.x, preview_rect.y, preview_rect.width // 2, preview_rect.height), border_top_left_radius=8, border_bottom_left_radius=8)
            pygame.draw.rect(screen, right, pygame.Rect(preview_rect.centerx, preview_rect.y, preview_rect.width // 2, preview_rect.height), border_top_right_radius=8, border_bottom_right_radius=8)
            pygame.draw.rect(screen, (255, 255, 255) if selected else (190, 206, 228), preview_rect, 2, border_radius=8)
            label = self.small_font.render(text, True, (62, 72, 98))
            screen.blit(label, (preview_rect.right + 16, rect.centery - label.get_height() // 2))
        self._draw_button(screen, self.filter_start, self.manager.t("ring_flight.filter.start"), (92, 152, 114))

    def _draw_home(self, screen):
        title = self.title_font.render(self.manager.t("ring_flight.title"), True, (34, 60, 96))
        subtitle = self.sub_font.render(self.manager.t("ring_flight.play.guide"), True, (96, 114, 142))
        hint = self.body_font.render(self.manager.t("ring_flight.filter.pick"), True, (52, 76, 110))
        screen.blit(title, (self.width // 2 - title.get_width() // 2, 82))
        screen.blit(subtitle, (self.width // 2 - subtitle.get_width() // 2, 140))
        screen.blit(hint, (self.width // 2 - hint.get_width() // 2, 184 + self.HOME_VERTICAL_UNIT * 3))
        self._draw_filter_option(screen, self.filter_lr, self.manager.t("ring_flight.filter.lr"), RED_FILTER[:3], BLUE_FILTER[:3], self.filter_direction == FILTER_LR)
        self._draw_filter_option(screen, self.filter_rl, self.manager.t("ring_flight.filter.rl"), BLUE_FILTER[:3], RED_FILTER[:3], self.filter_direction == FILTER_RL)
        self._draw_button(screen, self.btn_help, self.manager.t("ring_flight.home.help"), (124, 140, 168))
        self._draw_button(screen, self.btn_back, self.manager.t("common.back"), (86, 116, 170))

    def _draw_help(self, screen):
        title = self.title_font.render(self.manager.t("ring_flight.help.title"), True, (34, 60, 96))
        screen.blit(title, (self.width // 2 - title.get_width() // 2, 76))
        for idx, key in enumerate(("ring_flight.help.step1", "ring_flight.help.step2", "ring_flight.help.step3")):
            line = self.body_font.render(f"{idx + 1}. {self.manager.t(key)}", True, (58, 84, 118))
            screen.blit(line, (96, 196 + idx * 92))
        self._draw_button(screen, self.help_ok, self.manager.t("ring_flight.help.ok"), (244, 208, 120), text_color=(92, 76, 34))

    def _draw_target_indicator(self, screen):
        text = self.manager.t("ring_flight.target.inline", layer=self.manager.t(self._current_target_key()))
        label = self.small_font.render(text, True, (44, 60, 88))
        screen.blit(label, (self.width // 2 - label.get_width() // 2, 50))

    def _draw_plane(self, surface, plane_rect, horizontal_shift):
        plane = plane_rect.copy()
        plane = plane.move(horizontal_shift, 0)
        drift = int(round(2 * pygame.math.Vector2(1, 0).rotate(self._visual_phase * 80).y))
        plane.y += drift
        nose = (plane.centerx, plane.top - 12)
        body = [
            (plane.centerx - 7, plane.bottom - 4),
            (plane.centerx - 8, plane.centery + 10),
            (plane.centerx - 5, plane.top + 10),
            nose,
            (plane.centerx + 5, plane.top + 10),
            (plane.centerx + 8, plane.centery + 10),
            (plane.centerx + 7, plane.bottom - 4),
            (plane.centerx, plane.bottom - 12),
        ]
        wing = [
            (plane.left + 6, plane.centery + 4),
            (plane.centerx - 8, plane.centery - 2),
            (plane.centerx + 8, plane.centery - 2),
            (plane.right - 6, plane.centery + 4),
            (plane.centerx + 10, plane.centery + 10),
            (plane.centerx - 10, plane.centery + 10),
        ]
        tail = [
            (plane.centerx - 14, plane.bottom - 2),
            (plane.centerx - 5, plane.bottom - 12),
            (plane.centerx + 5, plane.bottom - 12),
            (plane.centerx + 14, plane.bottom - 2),
            (plane.centerx + 4, plane.bottom - 4),
            (plane.centerx - 4, plane.bottom - 4),
        ]
        pygame.draw.polygon(surface, (255, 255, 255, 255), wing)
        pygame.draw.polygon(surface, (255, 255, 255, 255), tail)
        pygame.draw.polygon(surface, (255, 255, 255, 255), body)
        pygame.draw.line(surface, (255, 255, 255, 255), (plane.centerx, plane.top + 4), (plane.centerx, plane.bottom - 8), 2)

    def _draw_ring_outline(self, surface, display, horizontal_shift):
        center = (int(display["center"][0] - self.play_area.x + horizontal_shift), int(display["center"][1] - self.play_area.y))
        pygame.draw.circle(surface, (255, 255, 255, 255), center, display["radius"], display["thickness"])

    def _draw_ring_sprite(self, screen, display):
        half_shift = max(4, display["disparity"] // 2)
        padding = display["thickness"] + half_shift + 8
        size = display["radius"] * 2 + padding * 2
        local_left = pygame.Surface((size, size), pygame.SRCALPHA)
        local_right = pygame.Surface((size, size), pygame.SRCALPHA)
        center = (size // 2, size // 2)
        pygame.draw.circle(local_left, (255, 255, 255, 255), (center[0] - half_shift, center[1]), display["radius"], display["thickness"])
        pygame.draw.circle(local_right, (255, 255, 255, 255), (center[0] + half_shift, center[1]), display["radius"], display["thickness"])
        left_filtered = apply_filter(local_left, self.mode, self.filter_direction, "left")
        right_filtered = apply_filter(local_right, self.mode, self.filter_direction, "right")
        ring_layer = blend_filtered_patterns(
            (size, size),
            left_filtered,
            (0, 0),
            right_filtered,
            (0, 0),
            crop_border=half_shift,
            use_offset_crop=False,
        )
        screen.blit(ring_layer, (display["center"][0] - size // 2, display["center"][1] - size // 2))

    def _draw_glasses_play_content(self, screen):
        pygame.draw.rect(screen, (255, 255, 255), self.play_area, 2, border_radius=20)
        for display in self._display_rings():
            self._draw_ring_sprite(screen, display)
        plane_shift = max(4, self.PLANE_DISPARITY // 2)
        plane_world = self._plane_rect().inflate(30, 28)
        plane_world.y -= 14
        plane_world = plane_world.clip(self.play_area)
        plane_local = plane_world.move(-plane_world.x, -plane_world.y)
        local_left = pygame.Surface(plane_world.size, pygame.SRCALPHA)
        local_right = pygame.Surface(plane_world.size, pygame.SRCALPHA)
        self._draw_plane(local_left, plane_local, -plane_shift)
        self._draw_plane(local_right, plane_local, plane_shift)
        left_filtered = apply_filter(local_left, self.mode, self.filter_direction, "left")
        right_filtered = apply_filter(local_right, self.mode, self.filter_direction, "right")
        plane_layer = blend_filtered_patterns(
            plane_world.size,
            left_filtered,
            (0, 0),
            right_filtered,
            (0, 0),
            crop_border=plane_shift,
            use_offset_crop=False,
        )
        screen.blit(plane_layer, plane_world.topleft)

    def _draw_play(self, screen):
        remaining = max(0, int(self.session.session_seconds - self.session.session_elapsed))
        timer = self.body_font.render(self.manager.t("ring_flight.time", sec=f"{remaining // 60:02d}:{remaining % 60:02d}"), True, (86, 116, 170))
        target_text = self.small_font.render(
            self.manager.t("ring_flight.target.inline", layer=self.manager.t(self._current_target_key())),
            True,
            (44, 60, 88),
        )
        score = self.body_font.render(self.manager.t("ring_flight.score", score=self.scoring.score), True, (44, 60, 88))
        streak = self.small_font.render(self.manager.t("ring_flight.streak", n=self.scoring.best_streak), True, (86, 104, 130))
        mode = self.body_font.render(self.manager.t("ring_flight.mode.glasses"), True, (44, 60, 88))
        direction_key = "ring_flight.direction_tip" if self.filter_direction == FILTER_LR else "ring_flight.direction_tip_rl"
        direction = self.small_font.render(self.manager.t(direction_key), True, (86, 104, 130))
        glasses_tip = self.small_font.render(self.manager.t("ring_flight.glasses_tip"), True, (86, 104, 130))
        screen.blit(mode, (24, 18))
        screen.blit(glasses_tip, (24, 46))
        screen.blit(direction, (24, 68))
        screen.blit(timer, (self.width // 2 - timer.get_width() // 2, 18))
        screen.blit(target_text, (self.width // 2 - target_text.get_width() // 2, 50))
        score_x = self.btn_home.left - 20 - score.get_width()
        streak_x = self.btn_home.left - 20 - streak.get_width()
        screen.blit(score, (score_x, 18))
        screen.blit(streak, (streak_x, 48))
        self._draw_glasses_play_content(screen)
        if self.feedback_text and time.time() <= self.feedback_until:
            fb = self.option_font.render(self.feedback_text, True, self.feedback_color)
            screen.blit(fb, (self.width // 2 - fb.get_width() // 2, self.play_area.bottom + 20))
        self._draw_button(screen, self.btn_home, self.manager.t("common.back"), (86, 116, 170))

    def _draw_result(self, screen):
        title = self.title_font.render(self.manager.t("ring_flight.result.title"), True, (34, 60, 96))
        screen.blit(title, (self.width // 2 - title.get_width() // 2, 84))
        lines = [
            self.manager.t("ring_flight.result.duration", sec=self.final_stats.get("duration", 0)),
            self.manager.t("ring_flight.result.success", n=self.final_stats.get("success", 0)),
            self.manager.t("ring_flight.result.wrong", n=self.final_stats.get("wrong", 0)),
            self.manager.t("ring_flight.result.accuracy", value=self.final_stats.get("accuracy", 0.0)),
            self.manager.t("ring_flight.result.score", n=self.final_stats.get("score", 0)),
            self.manager.t("ring_flight.result.switches", n=self.final_stats.get("switches", 0)),
            self.manager.t("ring_flight.result.mode", mode=self.manager.t("ring_flight.mode.glasses")),
            self.manager.t(
                "ring_flight.result.filter",
                direction=self._filter_direction_label(self.final_stats.get("filter_direction", FILTER_LR)),
            ),
        ]
        for idx, text in enumerate(lines):
            line = self.body_font.render(text, True, (66, 84, 114))
            screen.blit(line, (self.width // 2 - line.get_width() // 2, 166 + idx * 32))
        self._draw_button(screen, self.btn_continue, self.manager.t("ring_flight.result.continue"), (84, 148, 108))
        self._draw_button(screen, self.btn_exit, self.manager.t("ring_flight.result.exit"), (120, 134, 168))

    def handle_events(self, events):
        for event in events:
            if self.show_filter_picker:
                if event.type == pygame.KEYDOWN and event.key in (pygame.K_LEFT, pygame.K_RIGHT):
                    self.filter_direction = FILTER_RL if self.filter_direction == FILTER_LR else FILTER_LR
                elif event.type == pygame.KEYDOWN and event.key in (pygame.K_RETURN, pygame.K_SPACE):
                    self.show_filter_picker = False
                    self.mode = self.MODE_GLASSES
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
                        self.mode = self.MODE_GLASSES
                        self._start_game()
                    elif event.key == pygame.K_h:
                        self.state = self.STATE_HELP
                elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    pos = getattr(event, "pos", pygame.mouse.get_pos())
                    if self.filter_lr.collidepoint(pos):
                        self.mode = self.MODE_GLASSES
                        self.filter_direction = FILTER_LR
                        self._start_game()
                    elif self.filter_rl.collidepoint(pos):
                        self.mode = self.MODE_GLASSES
                        self.filter_direction = FILTER_RL
                        self._start_game()
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
                    if event.key == pygame.K_ESCAPE:
                        self.manager.set_scene("category")
                    elif event.key == pygame.K_LEFT:
                        self.plane_x -= 56
                    elif event.key == pygame.K_RIGHT:
                        self.plane_x += 56
                    elif self.awaiting_selection and event.key in (pygame.K_RETURN, pygame.K_SPACE):
                        self._start_fly_through()
                elif event.type == pygame.MOUSEMOTION:
                    self.plane_x = event.pos[0]
                elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    pos = getattr(event, "pos", pygame.mouse.get_pos())
                    if self.btn_home.collidepoint(pos):
                        self.manager.set_scene("category")
                    else:
                        self.plane_x = pos[0]
                        if self.awaiting_selection:
                            self._start_fly_through()
                self.plane_x = max(self.play_area.left + 34, min(self.play_area.right - 34, self.plane_x))
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
            self._visual_phase += 0.05 * self.frame_scale()
            if self.session.is_complete():
                self._finish_game()
                return
            if self.fly_through:
                if now - self.fly_through["started_at"] >= self.fly_through["duration"]:
                    result = self.fly_through["result"]
                    self.fly_through = None
                    self._finalize_wave_result(result)
                return
            if not self.awaiting_selection:
                step = self.RING_SPEED * self.frame_scale()
                for ring in self.wave.get("rings", []):
                    ring["progress"] = min(self.SELECT_PROGRESS, ring["progress"] + step)
                if self.wave.get("rings") and all(ring["progress"] >= self.SELECT_PROGRESS for ring in self.wave["rings"]):
                    self.awaiting_selection = True
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

