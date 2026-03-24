import math
import time
from datetime import datetime

import pygame

from core.base_scene import BaseScene
from games.common.anaglyph import (
    BLUE_FILTER,
    FILTER_LR,
    FILTER_RL,
    GLASSES_BUTTON_COLOR,
    MODE_GLASSES,
    RED_FILTER,
    SUBTRACTIVE_BACKGROUND,
    apply_filter,
    blend_filtered_patterns,
)
from ..services import PopNearestBoardService, PopNearestScoringService, PopNearestSessionService


class PopNearestScene(BaseScene):
    STATE_HOME = "home"
    STATE_HELP = "help"
    STATE_PLAY = "play"
    STATE_RESULT = "result"
    MODE_GLASSES = MODE_GLASSES
    SHOT_DURATION = 0.22
    IMPACT_DURATION = 0.32

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
        self.group_data = {}
        self.active_shot = None
        self.impact_effect = None
        self.pending_group_advance = False
        self.pending_finish = False
        self.last_group_started_at = 0.0
        self._balloon_surface_cache = {}
        self.board_service = PopNearestBoardService()
        self.scoring = PopNearestScoringService()
        self.session = PopNearestSessionService(session_seconds=self._session_seconds(), group_seconds=12)
        self._refresh_fonts()
        self._build_ui()

    def _refresh_fonts(self):
        self.title_font = self.create_font(52)
        self.sub_font = self.create_font(24)
        self.option_font = self.create_font(28)
        self.body_font = self.create_font(22)
        self.small_font = self.create_font(18)

    def _build_ui(self):
        card_w = min(560, self.width - 120)
        start_x = self.width // 2 - card_w // 2
        self.btn_start = pygame.Rect(start_x, 208, card_w, 58)
        self.btn_help = pygame.Rect(start_x, 282, card_w, 58)
        self.btn_back = pygame.Rect(self.width - 110, 18, 88, 36)
        self.btn_continue = pygame.Rect(self.width // 2 - 210, self.height - 100, 180, 48)
        self.btn_exit = pygame.Rect(self.width // 2 + 30, self.height - 100, 180, 48)
        self.help_ok = pygame.Rect(self.width // 2 - 90, self.height - 90, 180, 54)
        self.filter_modal = pygame.Rect(self.width // 2 - 250, self.height // 2 - 128, 500, 220)
        self.filter_lr = pygame.Rect(self.filter_modal.x + 24, self.filter_modal.y + 68, 210, 46)
        self.filter_rl = pygame.Rect(self.filter_modal.x + 266, self.filter_modal.y + 68, 210, 46)
        self.filter_start = pygame.Rect(self.filter_modal.centerx - 90, self.filter_modal.y + 150, 180, 44)
        self.play_area = pygame.Rect(70, 130, self.width - 140, self.height - 250)
        self.feedback_anchor_y = self.height - 118
        self.bow_y = self.height - 52
        default_bow_x = getattr(self, "bow_x", self.width // 2)
        self.bow_x = max(self.play_area.left + 30, min(self.play_area.right - 30, default_bow_x))

    def _session_seconds(self):
        try:
            minutes = int(self.manager.settings.get("session_duration_minutes", 5))
        except (TypeError, ValueError):
            minutes = 5
        return max(60, minutes * 60)

    def on_resize(self, width, height):
        self.width = width
        self.height = height
        self._build_ui()
        if self.state == self.STATE_PLAY:
            self._new_group()

    def reset(self):
        self.state = self.STATE_HOME
        self.mode = self.MODE_GLASSES
        self.filter_direction = FILTER_LR
        self.show_filter_picker = False
        self.feedback_text = ""
        self.feedback_until = 0.0
        self.final_stats = {}
        self.group_data = {}
        self.active_shot = None
        self.impact_effect = None
        self.pending_group_advance = False
        self.pending_finish = False
        self.bow_x = self.width // 2
        self.scoring.reset()
        self.session.session_seconds = self._session_seconds()
        self.session.reset()

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

    def _draw_filter_picker(self, screen):
        overlay = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        overlay.fill((24, 32, 46, 136))
        screen.blit(overlay, (0, 0))
        pygame.draw.rect(screen, (249, 251, 255), self.filter_modal, border_radius=18)
        title = self.sub_font.render(self.manager.t("pop_nearest.filter.pick"), True, (52, 70, 100))
        screen.blit(title, (self.filter_modal.centerx - title.get_width() // 2, self.filter_modal.y + 20))
        options = (
            (self.filter_lr, self.manager.t("pop_nearest.filter.lr"), RED_FILTER[:3], BLUE_FILTER[:3], self.filter_direction == FILTER_LR),
            (self.filter_rl, self.manager.t("pop_nearest.filter.rl"), BLUE_FILTER[:3], RED_FILTER[:3], self.filter_direction == FILTER_RL),
        )
        for rect, text, left, right, selected in options:
            self._draw_button(screen, rect, "", (244, 247, 255), text_color=(62, 72, 98), selected=selected)
            preview_rect = pygame.Rect(rect.x + 16, rect.y + 10, 56, rect.height - 20)
            pygame.draw.rect(screen, left, pygame.Rect(preview_rect.x, preview_rect.y, preview_rect.width // 2, preview_rect.height), border_top_left_radius=8, border_bottom_left_radius=8)
            pygame.draw.rect(screen, right, pygame.Rect(preview_rect.centerx, preview_rect.y, preview_rect.width // 2, preview_rect.height), border_top_right_radius=8, border_bottom_right_radius=8)
            pygame.draw.rect(screen, (255, 255, 255) if selected else (190, 206, 228), preview_rect, 2, border_radius=8)
            label = self.small_font.render(text, True, (62, 72, 98))
            screen.blit(label, (preview_rect.right + 16, rect.centery - label.get_height() // 2))
        self._draw_button(screen, self.filter_start, self.manager.t("pop_nearest.filter.start"), (92, 152, 114))

    def _play_sound(self, method_name):
        sound_manager = getattr(self.manager, "sound_manager", None)
        method = getattr(sound_manager, method_name, None) if sound_manager else None
        if method:
            method()

    def _set_feedback(self, key, color):
        self.feedback_text = self.manager.t(key)
        self.feedback_color = color
        self.feedback_until = time.time() + 1.0

    def _set_bow_x(self, x):
        self.bow_x = max(self.play_area.left + 30, min(self.play_area.right - 30, int(x)))

    def _pick_shot_balloon(self):
        candidates = []
        for idx, balloon in enumerate(self.group_data.get("balloons", [])):
            if balloon.get("popped"):
                continue
            display = self._balloon_display_state(balloon)
            center_x, center_y = display["center"]
            lane_half_width = balloon["radius"] + max(8, balloon["disparity"] // 2)
            if abs(self.bow_x - center_x) <= lane_half_width:
                candidates.append((balloon["depth_rank"], center_y, idx, display))
        if not candidates:
            return None, None
        candidates.sort(key=lambda item: (item[0], -item[1]))
        _, _, idx, display = candidates[0]
        return idx, display

    def _fire_vertical_shot(self):
        if self.active_shot is not None:
            return
        balloon_index, display = self._pick_shot_balloon()
        miss = balloon_index is None
        target_rank = self._target_rank()
        shot_correct = False if miss else self.group_data["balloons"][balloon_index]["depth_rank"] == target_rank
        self.active_shot = {
            "balloon_index": balloon_index,
            "correct": shot_correct,
            "miss": miss,
            "started_at": time.time(),
            "duration": self.SHOT_DURATION,
            "shot_x": self.bow_x,
            "target_y": self.play_area.top + 18 if miss else display["center"][1],
        }

    def _new_group(self):
        self.group_data = self.board_service.create_group(self.play_area, self.session.completed_groups + 1)
        self.last_group_started_at = time.time()
        self.active_shot = None
        self.impact_effect = None
        self.pending_group_advance = False
        self.pending_finish = False

    def _start_game(self):
        self.state = self.STATE_PLAY
        self.scoring.reset()
        self.session.session_seconds = self._session_seconds()
        self.session.reset()
        self.session.start()
        self.feedback_text = ""
        self._new_group()

    def _save_result(self):
        data_manager = getattr(self.manager, "data_manager", None)
        if not data_manager:
            return
        total = self.scoring.correct_pops + self.scoring.wrong_pops
        data_manager.save_training_session(
            {
                "timestamp": datetime.now().isoformat(),
                "game_id": "stereopsis.pop_nearest",
                "difficulty_level": 3,
                "total_questions": total,
                "correct_count": self.scoring.correct_pops,
                "wrong_count": self.scoring.wrong_pops,
                "duration_seconds": float(self.final_stats.get("duration", 0)),
                "accuracy_rate": self.final_stats.get("accuracy", 0.0),
                "training_metrics": {
                    "depth_order_accuracy": self.final_stats.get("accuracy", 0.0),
                    "correct_pops": self.final_stats.get("success", 0),
                    "wrong_pops": self.final_stats.get("wrong", 0),
                    "best_streak": self.final_stats.get("best_streak", 0),
                    "avg_pop_time": self.final_stats.get("avg_pop_time", 0.0),
                    "groups_cleared": self.final_stats.get("groups", 0),
                },
            }
        )

    def _finish_game(self):
        self.state = self.STATE_RESULT
        self.final_stats = {
            "duration": int(self.session.session_elapsed),
            "success": self.scoring.correct_pops,
            "wrong": self.scoring.wrong_pops,
            "accuracy": self.scoring.accuracy(),
            "score": self.scoring.score,
            "groups": self.scoring.groups_cleared,
            "best_streak": self.scoring.best_streak,
            "avg_pop_time": self.scoring.average_pop_time(),
            "filter_direction": self.filter_direction,
        }
        self._play_sound("play_completed")
        self._save_result()

    def _current_elapsed(self):
        return self.session.session_elapsed

    def _balloon_display_state(self, balloon):
        center = self.board_service.display_center(balloon, self._current_elapsed())
        return {
            "center": center,
            "radius": balloon["radius"],
            "disparity": balloon["disparity"],
        }

    def _balloon_surface(self, radius):
        cached = self._balloon_surface_cache.get(radius)
        if cached is not None:
            return cached
        size = radius * 2 + 24
        surface = pygame.Surface((size, size + radius // 2 + 12), pygame.SRCALPHA)
        center = (size // 2, size // 2 + 2)
        pygame.draw.circle(surface, (255, 255, 255), center, radius)
        pygame.draw.circle(surface, (255, 255, 255), (center[0] - radius // 3, center[1] - radius // 3), max(4, radius // 5))
        knot_y = center[1] + radius
        pygame.draw.line(surface, (255, 255, 255), (center[0], knot_y), (center[0] - 3, knot_y + 8), 3)
        pygame.draw.arc(surface, (255, 255, 255), pygame.Rect(center[0] - 8, knot_y + 2, 16, radius // 2), 0, math.pi, 2)
        self._balloon_surface_cache[radius] = surface
        return surface

    def _draw_stereo_surface(self, screen, surface, center, disparity):
        rect = surface.get_rect(center=center)
        left = apply_filter(surface, self.mode, self.filter_direction, "left")
        right = apply_filter(surface, self.mode, self.filter_direction, "right")
        crop_x = max(2, disparity // 3)
        half = disparity // 2
        local_size = (surface.get_width() + disparity + crop_x * 2, surface.get_height() + crop_x * 2)
        blended = blend_filtered_patterns(
            local_size,
            left,
            (crop_x, crop_x),
            right,
            (crop_x + disparity, crop_x),
            crop_border=(0, 0),
            use_offset_crop=False,
        )
        screen.blit(blended, (rect.x - half - crop_x, rect.y - crop_x))

    def _draw_balloons(self, screen):
        for balloon in self.group_data.get("balloons", []):
            if balloon.get("popped"):
                continue
            display = self._balloon_display_state(balloon)
            self._draw_stereo_surface(screen, self._balloon_surface(display["radius"]), display["center"], display["disparity"])

    def _draw_bow(self, screen):
        x, y = self.bow_x, self.bow_y
        wood = (236, 192, 112)
        wood_shadow = (178, 122, 64)
        string_color = (255, 247, 226)
        grip_rect = pygame.Rect(x - 6, y - 8, 12, 24)
        pygame.draw.arc(screen, wood_shadow, pygame.Rect(x - 37, y - 25, 74, 50), math.pi, math.tau, 6)
        pygame.draw.arc(screen, wood, pygame.Rect(x - 36, y - 24, 72, 48), math.pi, math.tau, 4)
        pygame.draw.rect(screen, wood_shadow, grip_rect.inflate(2, 2), border_radius=6)
        pygame.draw.rect(screen, wood, grip_rect, border_radius=6)
        pygame.draw.line(screen, string_color, (x - 30, y), (x + 30, y), 2)
        pygame.draw.line(screen, string_color, (x - 2, y - 16), (x - 2, y + 14), 2)
        pygame.draw.line(screen, string_color, (x + 2, y - 16), (x + 2, y + 14), 2)

    def _shot_start(self):
        return self.bow_x, self.bow_y - 36

    def _target_rank(self):
        return self.board_service.current_target_rank(self.group_data.get("balloons", []))

    def _resolve_shot(self):
        shot = self.active_shot
        if shot is None:
            return
        if shot.get("miss"):
            self.impact_effect = {
                "correct": False,
                "center": (shot["shot_x"], shot["target_y"]),
                "started_at": time.time(),
                "duration": self.IMPACT_DURATION,
            }
            self.scoring.on_wrong()
            self._play_sound("play_wrong")
            self._set_feedback("pop_nearest.feedback.miss", (255, 168, 148))
            self.active_shot = None
            return
        balloon = self.group_data["balloons"][shot["balloon_index"]]
        center = self._balloon_display_state(balloon)["center"]
        self.impact_effect = {
            "correct": shot["correct"],
            "center": center,
            "started_at": time.time(),
            "duration": self.IMPACT_DURATION,
        }
        if shot["correct"]:
            balloon["popped"] = True
            self.scoring.on_correct(max(0.0, time.time() - self.last_group_started_at))
            self._play_sound("play_correct")
            self._set_feedback("pop_nearest.feedback.correct", (255, 246, 164))
            if self.board_service.current_target_rank(self.group_data["balloons"]) is None:
                self.scoring.on_group_cleared()
                self.session.next_group()
                if self.session.is_complete():
                    self.pending_finish = True
                else:
                    self.pending_group_advance = True
        else:
            self.scoring.on_wrong()
            self._play_sound("play_wrong")
            self._set_feedback("pop_nearest.feedback.wrong", (255, 168, 148))
        self.active_shot = None

    def _draw_active_shot(self, screen):
        shot = self.active_shot
        if shot is None:
            return
        progress = min(1.0, max(0.0, (time.time() - shot["started_at"]) / shot["duration"]))
        start_x, start_y = self._shot_start()
        x = shot["shot_x"]
        # Make the arrow leave the bow decisively, then settle before impact.
        eased = 1.0 - pow(1.0 - progress, 3)
        y = start_y + (shot["target_y"] - start_y) * eased
        wobble = math.sin(progress * math.pi * 2.6) * (1.8 * (1.0 - progress))
        x += wobble
        trail_len = 20
        trail_start = (int(x), max(self.play_area.top, int(y) + trail_len))
        trail_end = (int(x), min(self.play_area.bottom, int(y) + trail_len + 22))
        pygame.draw.line(screen, (255, 235, 168), trail_start, trail_end, 2)

        shaft_len = 36
        half_w = 3
        tip_y = int(y - shaft_len // 2)
        tail_y = int(y + shaft_len // 2)
        pygame.draw.line(screen, (255, 248, 210), (int(x), tip_y), (int(x), tail_y), 4)
        pygame.draw.line(screen, (224, 184, 92), (int(x) + 1, tip_y + 2), (int(x) + 1, tail_y - 2), 1)
        pygame.draw.polygon(
            screen,
            (255, 248, 210),
            [(int(x), tip_y - 12), (int(x) - 6, tip_y + 6), (int(x) + 6, tip_y + 6)],
        )
        feather_base_y = tail_y + 1
        feather_spread = 9 + int((1.0 - progress) * 2)
        pygame.draw.line(screen, (255, 240, 184), (int(x), feather_base_y), (int(x) - feather_spread, feather_base_y + 10), 2)
        pygame.draw.line(screen, (255, 240, 184), (int(x), feather_base_y), (int(x) + feather_spread, feather_base_y + 10), 2)
        pygame.draw.line(screen, (255, 240, 184), (int(x), feather_base_y - 1), (int(x), feather_base_y + 11), 1)

    def _draw_impact_effect(self, screen):
        effect = self.impact_effect
        if not effect:
            return
        progress = (time.time() - effect["started_at"]) / effect["duration"]
        if progress >= 1.0:
            return
        cx, cy = effect["center"]
        if effect["correct"]:
            warm = (255, 243, 160)
            hot = (255, 206, 124)
            ring_radius = 18 + int(progress * 28)
            core_radius = max(8, 18 - int(progress * 10))
            pygame.draw.circle(screen, warm, (cx, cy), ring_radius, max(1, 5 - int(progress * 3)))
            pygame.draw.circle(screen, hot, (cx, cy), core_radius)
            for angle in range(0, 360, 45):
                radians = math.radians(angle)
                start = (
                    int(cx + math.cos(radians) * (12 + progress * 8)),
                    int(cy + math.sin(radians) * (12 + progress * 8)),
                )
                end = (
                    int(cx + math.cos(radians) * (22 + progress * 20)),
                    int(cy + math.sin(radians) * (22 + progress * 20)),
                )
                pygame.draw.line(screen, warm, start, end, 3)
        else:
            color = (255, 144, 144)
            offset = 10 + int(progress * 6)
            pygame.draw.line(screen, color, (cx - offset, cy - offset), (cx + offset, cy + offset), 4)
            pygame.draw.line(screen, color, (cx - offset, cy + offset), (cx + offset, cy - offset), 4)

    def _update_impact_state(self):
        effect = self.impact_effect
        if not effect:
            return
        progress = (time.time() - effect["started_at"]) / effect["duration"]
        if progress < 1.0:
            return
        self.impact_effect = None
        if self.pending_finish:
            self.pending_finish = False
            self._finish_game()
        elif self.pending_group_advance:
            self.pending_group_advance = False
            self._new_group()

    def _draw_feedback(self, screen):
        if not (self.feedback_text and time.time() <= self.feedback_until):
            return
        feedback = self.body_font.render(self.feedback_text, True, self.feedback_color)
        shadow = self.body_font.render(self.feedback_text, True, (28, 18, 34))
        padding_x = 16
        padding_y = 8
        box = pygame.Rect(
            self.width // 2 - feedback.get_width() // 2 - padding_x,
            self.feedback_anchor_y - padding_y,
            feedback.get_width() + padding_x * 2,
            feedback.get_height() + padding_y * 2,
        )
        bubble = pygame.Surface(box.size, pygame.SRCALPHA)
        pygame.draw.rect(bubble, (22, 18, 34, 88), bubble.get_rect(), border_radius=12)
        screen.blit(bubble, box.topleft)
        pygame.draw.rect(screen, (244, 239, 228), box, 1, border_radius=12)
        screen.blit(shadow, (self.width // 2 - feedback.get_width() // 2 + 2, self.feedback_anchor_y + 2))
        screen.blit(feedback, (self.width // 2 - feedback.get_width() // 2, self.feedback_anchor_y))

    def _draw_play(self, screen):
        screen.fill(SUBTRACTIVE_BACKGROUND[:3])
        self._draw_balloons(screen)
        self._draw_active_shot(screen)
        self._draw_impact_effect(screen)
        self._draw_bow(screen)

        hud_primary = (42, 12, 72)
        hud_secondary = (88, 28, 92)
        hud_alert = (132, 18, 32)
        time_value = int(self.session.session_time_left() + 0.99)
        score = self.small_font.render(self.manager.t("pop_nearest.score", score=self.scoring.score), True, hud_primary)
        success = self.small_font.render(self.manager.t("pop_nearest.success", n=self.scoring.correct_pops), True, hud_secondary)
        groups = self.small_font.render(self.manager.t("pop_nearest.groups", n=self.scoring.groups_cleared), True, hud_secondary)
        mode = self.small_font.render(self.manager.t("pop_nearest.mode.glasses"), True, hud_primary)
        time_text = self.small_font.render(self.manager.t("pop_nearest.time", sec=time_value), True, hud_alert if time_value <= 30 else hud_primary)
        goal = self.small_font.render(self.manager.t("pop_nearest.goal"), True, hud_secondary)
        confirm = self.small_font.render(self.manager.t("pop_nearest.play.confirm"), True, hud_secondary)
        screen.blit(score, (26, 18))
        screen.blit(success, (26, 44))
        screen.blit(groups, (26, 70))
        screen.blit(mode, (26, 96))
        screen.blit(time_text, (self.width // 2 - time_text.get_width() // 2, 18))
        screen.blit(goal, (self.width // 2 - goal.get_width() // 2, 44))
        screen.blit(confirm, (self.width // 2 - confirm.get_width() // 2, 70))
        self._draw_button(screen, self.btn_back, self.manager.t("common.back"), GLASSES_BUTTON_COLOR)
        self._draw_feedback(screen)

    def _draw_home(self, screen):
        screen.fill((235, 245, 255))
        title = self.title_font.render(self.manager.t("pop_nearest.title"), True, (34, 60, 96))
        subtitle = self.sub_font.render(self.manager.t("pop_nearest.goal"), True, (96, 114, 142))
        screen.blit(title, (self.width // 2 - title.get_width() // 2, 82))
        screen.blit(subtitle, (self.width // 2 - subtitle.get_width() // 2, 138))
        self._draw_button(screen, self.btn_start, self.manager.t("pop_nearest.home.start"), GLASSES_BUTTON_COLOR)
        self._draw_button(screen, self.btn_help, self.manager.t("pop_nearest.home.help"), (124, 140, 168))
        self._draw_button(screen, self.btn_back, self.manager.t("common.back"), (86, 116, 170))

    def _draw_help(self, screen):
        screen.fill((235, 245, 255))
        title = self.title_font.render(self.manager.t("pop_nearest.help.title"), True, (34, 60, 96))
        screen.blit(title, (self.width // 2 - title.get_width() // 2, 76))
        for idx, key in enumerate(("pop_nearest.help.step1", "pop_nearest.help.step2", "pop_nearest.help.step3")):
            line = self.body_font.render(f"{idx + 1}. {self.manager.t(key)}", True, (58, 84, 118))
            screen.blit(line, (88, 196 + idx * 92))
        self._draw_button(screen, self.help_ok, self.manager.t("pop_nearest.help.ok"), (244, 208, 120), text_color=(92, 76, 34))

    def _draw_result(self, screen):
        screen.fill((235, 245, 255))
        title = self.title_font.render(self.manager.t("pop_nearest.result.title"), True, (34, 60, 96))
        screen.blit(title, (self.width // 2 - title.get_width() // 2, 82))
        lines = (
            self.manager.t("pop_nearest.result.duration", sec=self.final_stats.get("duration", 0)),
            self.manager.t("pop_nearest.result.success", n=self.final_stats.get("success", 0)),
            self.manager.t("pop_nearest.result.wrong", n=self.final_stats.get("wrong", 0)),
            self.manager.t("pop_nearest.result.accuracy", value=self.final_stats.get("accuracy", 0.0)),
            self.manager.t("pop_nearest.result.score", n=self.final_stats.get("score", 0)),
            self.manager.t("pop_nearest.result.groups", n=self.final_stats.get("groups", 0)),
            self.manager.t("pop_nearest.result.best_streak", n=self.final_stats.get("best_streak", 0)),
            self.manager.t("pop_nearest.result.avg_pop_time", sec=self.final_stats.get("avg_pop_time", 0.0)),
        )
        for idx, line in enumerate(lines):
            label = self.body_font.render(line, True, (58, 84, 118))
            screen.blit(label, (self.width // 2 - label.get_width() // 2, 180 + idx * 42))
        self._draw_button(screen, self.btn_continue, self.manager.t("pop_nearest.result.continue"), (92, 152, 114))
        self._draw_button(screen, self.btn_exit, self.manager.t("pop_nearest.result.exit"), (124, 140, 168))

    def handle_events(self, events):
        for event in events:
            if self.show_filter_picker:
                if event.type == pygame.KEYDOWN:
                    if event.key in (pygame.K_LEFT, pygame.K_UP):
                        self.filter_direction = FILTER_LR
                    elif event.key in (pygame.K_RIGHT, pygame.K_DOWN):
                        self.filter_direction = FILTER_RL
                    elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
                        self.show_filter_picker = False
                        self._start_game()
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    if self.filter_lr.collidepoint(event.pos):
                        self.filter_direction = FILTER_LR
                    elif self.filter_rl.collidepoint(event.pos):
                        self.filter_direction = FILTER_RL
                    elif self.filter_start.collidepoint(event.pos):
                        self.show_filter_picker = False
                        self._start_game()
                continue

            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if self.state == self.STATE_HOME:
                    if self.btn_start.collidepoint(event.pos):
                        self.show_filter_picker = True
                    elif self.btn_help.collidepoint(event.pos):
                        self.state = self.STATE_HELP
                    elif self.btn_back.collidepoint(event.pos):
                        self.manager.set_scene("category")
                elif self.state == self.STATE_HELP:
                    if self.help_ok.collidepoint(event.pos):
                        self.state = self.STATE_HOME
                elif self.state == self.STATE_PLAY:
                    if self.btn_back.collidepoint(event.pos):
                        self.manager.set_scene("category")
                    elif self.active_shot is None:
                        self._set_bow_x(event.pos[0])
                        self._fire_vertical_shot()
                elif self.state == self.STATE_RESULT:
                    if self.btn_continue.collidepoint(event.pos):
                        self.show_filter_picker = True
                        self.state = self.STATE_HOME
                    elif self.btn_exit.collidepoint(event.pos):
                        self.manager.set_scene("menu")

            if event.type == pygame.MOUSEMOTION and self.state == self.STATE_PLAY:
                self._set_bow_x(event.pos[0])

            if event.type != pygame.KEYDOWN:
                continue
            if event.key == pygame.K_ESCAPE:
                if self.state == self.STATE_PLAY:
                    self.manager.set_scene("category")
                elif self.state == self.STATE_HELP:
                    self.state = self.STATE_HOME
                elif self.state == self.STATE_RESULT:
                    self.manager.set_scene("menu")
                else:
                    self.manager.set_scene("category")
                continue
            if self.state == self.STATE_HOME and event.key in (pygame.K_RETURN, pygame.K_SPACE):
                self.show_filter_picker = True
            elif self.state == self.STATE_HELP and event.key in (pygame.K_RETURN, pygame.K_SPACE):
                self.state = self.STATE_HOME
            elif self.state == self.STATE_PLAY:
                if event.key in (pygame.K_LEFT, pygame.K_UP):
                    self._set_bow_x(self.bow_x - 36)
                elif event.key in (pygame.K_RIGHT, pygame.K_DOWN):
                    self._set_bow_x(self.bow_x + 36)
                elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
                    self._fire_vertical_shot()
            elif self.state == self.STATE_RESULT and event.key in (pygame.K_RETURN, pygame.K_SPACE):
                self.show_filter_picker = True
                self.state = self.STATE_HOME

    def update(self):
        if self.state != self.STATE_PLAY:
            return
        self.session.tick()
        self._update_impact_state()
        if self.active_shot and (time.time() - self.active_shot["started_at"]) >= self.active_shot["duration"]:
            self._resolve_shot()
            if self.state != self.STATE_PLAY:
                return
        if self.pending_finish or self.pending_group_advance:
            return
        if self.session.is_complete():
            self._finish_game()
            return
        if self.session.is_group_timeout():
            self._play_sound("play_wrong")
            self._set_feedback("pop_nearest.feedback.timeout", (255, 168, 148))
            self.session.next_group()
            if self.session.is_complete():
                self._finish_game()
            else:
                self._new_group()

    def draw(self, screen):
        if self.state == self.STATE_HOME:
            self._draw_home(screen)
        elif self.state == self.STATE_HELP:
            self._draw_help(screen)
        elif self.state == self.STATE_PLAY:
            self._draw_play(screen)
        elif self.state == self.STATE_RESULT:
            self._draw_result(screen)
        if self.show_filter_picker:
            self._draw_filter_picker(screen)
