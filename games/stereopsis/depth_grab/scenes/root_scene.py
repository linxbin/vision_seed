import math
import time
from datetime import datetime

import pygame

from core.asset_loader import load_image_if_exists, project_path
from core.base_scene import BaseScene
from games.common.anaglyph import BLUE_FILTER, FILTER_LR, FILTER_RL, GLASSES_BUTTON_COLOR, MODE_GLASSES, RED_FILTER, SUBTRACTIVE_BACKGROUND, apply_filter, blend_filtered_patterns
from ..services import DepthGrabBoardService, DepthGrabScoringService, DepthGrabSessionService


class DepthGrabScene(BaseScene):
    STATE_HOME = "home"
    STATE_HELP = "help"
    STATE_PLAY = "play"
    STATE_RESULT = "result"
    MODE_GLASSES = MODE_GLASSES
    FILTER_LR = FILTER_LR
    FILTER_RL = FILTER_RL

    def __init__(self, manager):
        super().__init__(manager)
        self.width = 900
        self.height = 700
        self.state = self.STATE_HOME
        self.mode = self.MODE_GLASSES
        self.filter_direction = self.FILTER_LR
        self.show_filter_picker = False
        self.feedback_text = ""
        self.feedback_color = (255, 255, 255)
        self.feedback_until = 0.0
        self.final_stats = {}
        self._depth_phase = 0.0
        self.board_service = DepthGrabBoardService()
        self.scoring = DepthGrabScoringService()
        self.session = DepthGrabSessionService(self._session_seconds())
        self.round_data = {"targets": [], "correct_index": 0, "stage_index": 0}
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
        self.btn_start = pygame.Rect(start_x, 208, card_w, 58)
        self.btn_help = pygame.Rect(start_x, 282, card_w, 58)
        self.btn_back = pygame.Rect(self.width - 110, 18, 88, 36)
        self.btn_home = pygame.Rect(self.width - 110, 18, 88, 36)
        self.btn_continue = pygame.Rect(self.width // 2 - 210, self.height - 100, 180, 48)
        self.btn_exit = pygame.Rect(self.width // 2 + 30, self.height - 100, 180, 48)
        self.help_ok = pygame.Rect(self.width // 2 - 90, self.height - 90, 180, 54)
        self.filter_modal = pygame.Rect(self.width // 2 - 250, self.height // 2 - 128, 500, 220)
        self.filter_lr = pygame.Rect(self.filter_modal.x + 24, self.filter_modal.y + 68, 210, 46)
        self.filter_rl = pygame.Rect(self.filter_modal.x + 266, self.filter_modal.y + 68, 210, 46)
        self.filter_start = pygame.Rect(self.filter_modal.centerx - 90, self.filter_modal.y + 150, 180, 44)
        self.play_area = pygame.Rect(60, 128, self.width - 120, self.height - 250)

    def on_resize(self, width, height):
        self.width = width
        self.height = height
        self._build_ui()
        if self.state == self.STATE_PLAY:
            self._new_round()

    def reset(self):
        self.state = self.STATE_HOME
        self.mode = self.MODE_GLASSES
        self.filter_direction = self.FILTER_LR
        self.show_filter_picker = False
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
            label = self.option_font.render(text, True, text_color)
            icon = self._load_ui_icon(icon_name, light=sum(text_color) > 500) if icon_name else None
            gap = 8 if icon is not None else 0
            width = label.get_width() + (icon.get_width() + gap if icon is not None else 0)
            start_x = rect.centerx - width // 2
            if icon is not None:
                screen.blit(icon, (start_x, rect.centery - icon.get_height() // 2))
                start_x += icon.get_width() + gap
            screen.blit(label, (start_x, rect.centery - label.get_height() // 2))
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

    def _set_feedback(self, key, color):
        self.feedback_text = self.manager.t(key)
        self.feedback_color = color
        self.feedback_until = time.time() + 1.1

    def _play_sound(self, method_name):
        sound_manager = getattr(self.manager, "sound_manager", None)
        method = getattr(sound_manager, method_name, None) if sound_manager else None
        if method:
            method()

    def _new_round(self):
        self.round_data = self.board_service.create_round(self.play_area, self._stage_index())
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
            "score": self.scoring.score,
            "success": self.scoring.success_count,
            "wrong": self.scoring.failure_count,
            "accuracy": self.scoring.accuracy(),
            "avg_grab_time": self.scoring.average_reaction_time(),
            "best_streak": self.scoring.best_streak,
            "front_back_confusion_count": self.scoring.front_back_confusion_count,
            "stage_reached": self.scoring.stage_reached + 1,
            "mode": self.mode,
            "filter_direction": self.filter_direction,
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
                "game_id": "stereopsis.depth_grab",
                "difficulty_level": 4,
                "total_questions": total,
                "correct_count": self.scoring.success_count,
                "wrong_count": self.scoring.failure_count,
                "duration_seconds": float(self.final_stats.get("duration", 0)),
                "accuracy_rate": self.final_stats.get("accuracy", 0.0),
                "training_metrics": {
                    "depth_accuracy": self.final_stats.get("accuracy", 0.0),
                    "avg_grab_time": self.final_stats.get("avg_grab_time", 0.0),
                    "front_back_confusion_count": self.scoring.front_back_confusion_count,
                    "best_streak": self.scoring.best_streak,
                    "stage_reached": self.final_stats.get("stage_reached", 1),
                },
            }
        )

    def _go_category(self):
        self.manager.set_scene("category")

    def _go_menu(self):
        self.manager.set_scene("menu")

    def _draw_background(self, screen):
        if self.state == self.STATE_PLAY and self.mode == self.MODE_GLASSES:
            screen.fill(SUBTRACTIVE_BACKGROUND[:3])
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
        if self.state == self.STATE_PLAY:
            for idx in range(6):
                band_y = 150 + idx * 70 + math.sin(self._depth_phase * 0.6 + idx * 0.4) * 8
                pygame.draw.line(screen, (240, 247, 255), (90, int(band_y)), (self.width - 90, int(band_y)), 1)

    def _star_points(self, center, radius, tips, rotation):
        points = []
        inner_radius = radius * 0.46
        for idx in range(tips * 2):
            angle = rotation + (math.pi * idx / tips)
            current_radius = radius if idx % 2 == 0 else inner_radius
            points.append(
                (
                    center[0] + math.cos(angle) * current_radius,
                    center[1] + math.sin(angle) * current_radius,
                )
            )
        return points

    def _draw_star_shadow(self, surface, center, radius, variant, depth_rank):
        offset = 18 - depth_rank * 3
        shadow_center = (center[0] + offset, center[1] + offset)
        self._draw_star_shape(surface, shadow_center, radius, variant, (208, 220, 234))

    def _draw_star_shape(self, surface, center, radius, variant, color):
        points = self._star_points(center, radius, variant["tips"], variant["rotation"])
        pygame.draw.polygon(surface, color, points)
        return points

    def _target_display_state(self, target, idx):
        x, y = target["center"]
        radius = target["radius"]
        depth_rank = target.get("depth_rank", 0)
        layer_offset = target.get("layer_offset", 0)
        bob = math.sin(self._depth_phase * (1.3 + idx * 0.17) + idx) * (4 + depth_rank)
        x = int(x + math.cos(self._depth_phase * 0.7 + idx) * 4)
        y = int(y + bob + layer_offset)
        glasses_radius = radius + (6 if depth_rank == 0 else 3)
        return {
            "center": (x, y),
            "radius": radius,
            "glasses_radius": glasses_radius,
        }

    def _point_in_star(self, point, center, radius, variant):
        local_size = radius * 2 + 8
        local_surface = pygame.Surface((local_size, local_size), pygame.SRCALPHA)
        local_center = (local_size // 2, local_size // 2)
        points = self._star_points(local_center, radius, variant["tips"], variant["rotation"])
        pygame.draw.polygon(local_surface, (255, 255, 255), points)
        local_x = int(point[0] - center[0] + local_center[0])
        local_y = int(point[1] - center[1] + local_center[1])
        if not (0 <= local_x < local_size and 0 <= local_y < local_size):
            return False
        mask = pygame.mask.from_surface(local_surface)
        return bool(mask.get_at((local_x, local_y)))

    def _point_hits_target(self, point, target, idx):
        display = self._target_display_state(target, idx)
        center = display["center"]
        radius = display["radius"]
        variant = target.get("star_variant", {"tips": 5, "rotation": -1.57})
        if self.mode == self.MODE_GLASSES:
            eye_shift = max(5, target["disparity"] // 2)
            return (
                self._point_in_star(point, (center[0] - eye_shift, center[1]), display["glasses_radius"], variant)
                or self._point_in_star(point, (center[0] + eye_shift, center[1]), display["glasses_radius"], variant)
            )
        return self._point_in_star(point, center, radius, variant)

    def _draw_targets(self, screen):
        left = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        right = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        neutral = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        for idx, target in enumerate(self.round_data["targets"]):
            display = self._target_display_state(target, idx)
            x, y = display["center"]
            radius = display["radius"]
            variant = target["star_variant"]
            disparity = target["disparity"]
            eye_shift = max(5, disparity // 2)
            glasses_radius = display["glasses_radius"]
            self._draw_star_shape(left, (x - eye_shift, y), glasses_radius, variant, (255, 255, 255))
            self._draw_star_shape(right, (x + eye_shift, y), glasses_radius, variant, (255, 255, 255))
        screen.blit(neutral, (0, 0))
        left_filtered = apply_filter(left, self.mode, self.filter_direction, "left")
        right_filtered = apply_filter(right, self.mode, self.filter_direction, "right")
        blended = blend_filtered_patterns((self.width, self.height), left_filtered, (0, 0), right_filtered, (0, 0))
        screen.blit(blended, (0, 0))

    def _target_hit(self, pos):
        for idx, target in enumerate(self.round_data["targets"]):
            if self._point_hits_target(pos, target, idx):
                return idx
        return None

    def _resolve_click(self, pos):
        hit_index = self._target_hit(pos)
        if hit_index is None:
            return
        hit = self.round_data["targets"][hit_index]
        if hit_index == self.round_data["correct_index"]:
            gained = self.scoring.on_success(self.session.round_elapsed, self.round_data["stage_index"])
            self._set_feedback("depth_grab.feedback.correct", (90, 226, 132))
            self.feedback_text = f"{self.feedback_text}  +{gained}"
            self._play_sound("play_correct")
        else:
            self.scoring.on_failure(hit["depth_rank"])
            self._set_feedback("depth_grab.feedback.wrong", (238, 118, 118))
            self._play_sound("play_wrong")
        self._new_round()

    def _draw_home(self, screen):
        title = self.title_font.render(self.manager.t("depth_grab.title"), True, (38, 66, 108))
        screen.blit(title, (self.width // 2 - title.get_width() // 2, 86))
        self._draw_button(screen, self.btn_start, self.manager.t("depth_grab.home.start"), GLASSES_BUTTON_COLOR, icon_name="target")
        self._draw_button(screen, self.btn_help, self.manager.t("depth_grab.home.help"), (126, 142, 174), icon_name="question")
        self._draw_button(screen, self.btn_back, self.manager.t("common.back"), (88, 116, 168), icon_name="back_arrow")
        if self.show_filter_picker:
            modal = pygame.Surface((self.filter_modal.width, self.filter_modal.height), pygame.SRCALPHA)
            modal.fill((248, 253, 255, 238))
            screen.blit(modal, self.filter_modal.topleft)
            pygame.draw.rect(screen, (116, 148, 196), self.filter_modal, 2, border_radius=12)
            msg = self.body_font.render(self.manager.t("depth_grab.filter.pick"), True, (52, 76, 110))
            screen.blit(msg, (self.filter_modal.centerx - msg.get_width() // 2, self.filter_modal.y + 24))
            self._draw_filter_option(screen, self.filter_lr, self.manager.t("depth_grab.filter.lr"), RED_FILTER[:3], BLUE_FILTER[:3], self.filter_direction == self.FILTER_LR)
            self._draw_filter_option(screen, self.filter_rl, self.manager.t("depth_grab.filter.rl"), BLUE_FILTER[:3], RED_FILTER[:3], self.filter_direction == self.FILTER_RL)
            self._draw_button(screen, self.filter_start, self.manager.t("depth_grab.filter.start"), (86, 150, 108), icon_name="check")

    def _draw_help_step(self, screen, idx, y, text):
        pygame.draw.circle(screen, (255, 208, 124) if idx == 1 else (136, 198, 255) if idx == 2 else (162, 225, 162), (132, y + 18), 14)
        step = self.small_font.render(f"{idx}. {text}", True, (58, 84, 118))
        screen.blit(step, (160, y + 6))

    def _draw_help_demo(self, screen):
        demo_rect = pygame.Rect(self.width // 2 - 150, 455, 300, 120)
        panel = pygame.Surface((demo_rect.width, demo_rect.height), pygame.SRCALPHA)
        panel.fill((248, 252, 255, 228))
        screen.blit(panel, demo_rect.topleft)
        pygame.draw.rect(screen, (188, 212, 238), demo_rect, 2, border_radius=16)
        label = self.small_font.render(self.manager.t("depth_grab.help.demo"), True, (62, 86, 118))
        screen.blit(label, (demo_rect.centerx - label.get_width() // 2, demo_rect.y + 10))

        center = (demo_rect.centerx, demo_rect.centery + 12)
        front_variant = {"tips": 5, "rotation": -1.57}
        back_variant = {"tips": 5, "rotation": -1.32}
        self._draw_star_shape(screen, (center[0] - 58, center[1] + 10), 18, back_variant, (166, 198, 236))
        self._draw_star_shape(screen, (center[0] + 62, center[1] + 14), 16, back_variant, (180, 210, 242))
        self._draw_star_shape(screen, center, 28, front_variant, (255, 203, 98))
        pygame.draw.polygon(screen, (255, 255, 255), self._star_points(center, 28, 5, -1.57), 3)
        arrow = self.small_font.render(self.manager.t("depth_grab.help.tap_front"), True, (62, 86, 118))
        screen.blit(arrow, (demo_rect.centerx - arrow.get_width() // 2, demo_rect.bottom - 28))

    def _draw_help(self, screen):
        title = self.title_font.render(self.manager.t("depth_grab.help.title"), True, (42, 70, 110))
        screen.blit(title, (self.width // 2 - title.get_width() // 2, 76))
        self._draw_help_step(screen, 1, 190, self.manager.t("depth_grab.help.step1"))
        self._draw_help_step(screen, 2, 280, self.manager.t("depth_grab.help.step2"))
        self._draw_help_step(screen, 3, 370, self.manager.t("depth_grab.help.step3"))
        self._draw_help_demo(screen)
        self._draw_button(screen, self.help_ok, self.manager.t("depth_grab.help.ok"), (242, 214, 126), text_color=(104, 84, 42), icon_name="check")

    def _draw_play(self, screen):
        is_glasses_mode = self.mode == self.MODE_GLASSES
        hud_primary = (42, 12, 72) if is_glasses_mode else (55, 82, 122)
        hud_secondary = (88, 28, 92) if is_glasses_mode else (86, 104, 130)
        hud_alert = (132, 18, 32) if is_glasses_mode else (222, 74, 74)
        mode_text = self.manager.t("depth_grab.mode.glasses")
        remaining = max(0, int(self.session.session_seconds - self.session.session_elapsed))
        left_lines = [
            self.manager.t(self.board_service.stage_label_key(self.round_data["stage_index"])),
            self.manager.t(self.board_service.goal_label_key(self.round_data["stage_index"])),
        ]
        right_lines = []
        if is_glasses_mode:
            direction_key = "depth_grab.filter.lr" if self.filter_direction == self.FILTER_LR else "depth_grab.filter.rl"
            left_lines = [
                self.manager.t("depth_grab.glasses_tip"),
                self.manager.t(direction_key),
                self.manager.t(self.board_service.stage_label_key(self.round_data["stage_index"])),
                self.manager.t(self.board_service.goal_label_key(self.round_data["stage_index"])),
            ]
            right_lines = []
        self.draw_session_hud(
            screen,
            top_font=self.body_font,
            meta_font=self.small_font,
            left_title=mode_text,
            timer_text=self.manager.t("depth_grab.time", sec=f"{remaining // 60:02d}:{remaining % 60:02d}"),
            center_text=self.manager.t("depth_grab.score", score=self.scoring.score),
            left_lines=tuple(left_lines),
            right_lines=tuple(right_lines),
            play_area=self.play_area,
            timer_color=hud_alert if remaining <= 30 else hud_primary,
            center_color=hud_primary,
            left_title_color=hud_primary,
            meta_color=hud_secondary,
            meta_start_y=50,
        )
        guide = self.small_font.render(self.manager.t("depth_grab.play.guide"), True, hud_secondary)
        screen.blit(guide, (self.play_area.centerx - guide.get_width() // 2, max(98, self.play_area.y - 28)))
        self._draw_targets(screen)
        if self.feedback_text and time.time() <= self.feedback_until:
            fb = self.body_font.render(self.feedback_text, True, self.feedback_color)
            screen.blit(fb, (self.width // 2 - fb.get_width() // 2, self.play_area.bottom + 18))
        self._draw_button(screen, self.btn_home, self.manager.t("common.back"), (62, 52, 128) if is_glasses_mode else (86, 116, 170), icon_name="back_arrow")

    def _draw_result(self, screen):
        title = self.title_font.render(self.manager.t("depth_grab.result.title"), True, (42, 70, 110))
        screen.blit(title, (self.width // 2 - title.get_width() // 2, 100))
        mode_text = self.manager.t("depth_grab.mode.glasses")
        filter_text = "-"
        if self.final_stats.get("mode") == self.MODE_GLASSES:
            filter_text = self.manager.t("depth_grab.filter.lr" if self.final_stats.get("filter_direction") == self.FILTER_LR else "depth_grab.filter.rl")
        lines = [
            (self.manager.t("depth_grab.result.duration", sec=self.final_stats.get("duration", 0)), (58, 84, 118)),
            (self.manager.t("depth_grab.result.success", n=self.final_stats.get("success", 0)), (58, 84, 118)),
            (self.manager.t("depth_grab.result.wrong", n=self.final_stats.get("wrong", 0)), (58, 84, 118)),
            (self.manager.t("depth_grab.result.accuracy", value=self.final_stats.get("accuracy", 0.0)), (58, 84, 118)),
            (self.manager.t("depth_grab.result.score", n=self.final_stats.get("score", 0)), (58, 84, 118)),
            (self.manager.t("depth_grab.result.grab_time", sec=self.final_stats.get("avg_grab_time", 0.0)), (58, 84, 118)),
            (self.manager.t("depth_grab.result.confusion", n=self.final_stats.get("front_back_confusion_count", 0)), (58, 84, 118)),
            (self.manager.t("depth_grab.result.mode", mode=mode_text), (96, 114, 138)),
            (self.manager.t("depth_grab.result.filter", direction=filter_text), (96, 114, 138)),
        ]
        self.draw_two_column_stats(
            screen,
            font=self.body_font,
            entries=lines,
            top_y=184,
            left_x=self.width // 2 - 320,
            right_x=self.width // 2 + 24,
            column_width=296,
            rows_per_column=5,
            row_gap=38,
        )
        self._draw_button(screen, self.btn_continue, self.manager.t("depth_grab.result.continue"), (84, 148, 108), icon_name="check")
        self._draw_button(screen, self.btn_exit, self.manager.t("depth_grab.result.exit"), (120, 134, 168), icon_name="cross")

    def handle_events(self, events):
        for event in events:
            if self.show_filter_picker:
                if event.type == pygame.KEYDOWN:
                    if event.key in (pygame.K_LEFT, pygame.K_RIGHT):
                        self.filter_direction = self.FILTER_RL if self.filter_direction == self.FILTER_LR else self.FILTER_LR
                    elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
                        self.show_filter_picker = False
                        self._start_game()
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
                        self._start_game()
                continue
            if self.state == self.STATE_HOME:
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        self._go_category()
                    elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
                        self.mode = self.MODE_GLASSES
                        self.show_filter_picker = True
                    elif event.key == pygame.K_h:
                        self.state = self.STATE_HELP
                elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    pos = getattr(event, "pos", pygame.mouse.get_pos())
                    if self.btn_back.collidepoint(pos):
                        self._go_category()
                    elif self.btn_start.collidepoint(pos):
                        self.mode = self.MODE_GLASSES
                        self.show_filter_picker = True
                    elif self.btn_help.collidepoint(pos):
                        self.state = self.STATE_HELP
            elif self.state == self.STATE_HELP:
                if event.type == pygame.KEYDOWN and event.key in (pygame.K_ESCAPE, pygame.K_RETURN):
                    self.state = self.STATE_HOME
                elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1 and self.help_ok.collidepoint(getattr(event, "pos", pygame.mouse.get_pos())):
                    self.state = self.STATE_HOME
            elif self.state == self.STATE_PLAY:
                if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                    self._go_category()
                elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    pos = getattr(event, "pos", pygame.mouse.get_pos())
                    if self.btn_home.collidepoint(pos):
                        self._go_category()
                    else:
                        self._resolve_click(pos)
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
            self._depth_phase += 0.05 * self.frame_scale()
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
