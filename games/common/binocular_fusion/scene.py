import math
import random
import time
from dataclasses import dataclass

import pygame

from core.base_scene import BaseScene
from games.common.anaglyph import (
    BLUE_FILTER,
    FILTER_LR,
    FILTER_RL,
    GLASSES_BACKGROUND,
    MODE_GLASSES,
    RED_FILTER,
    apply_filter,
    blend_filtered_patterns,
)


@dataclass(frozen=True)
class FusionGameConfig:
    game_id: str
    category: str
    name: str
    name_key: str
    title_key: str
    subtitle_key: str
    guide_key: str
    metric_label_key: str
    help_steps: tuple[str, str, str]
    mechanic_type: str
    theme_color: tuple[int, int, int]


class _FusionMechanic:
    def __init__(self, scene):
        self.scene = scene
        self.success_count = 0
        self.fail_count = 0
        self.best_streak = 0
        self.streak = 0

    def start_task(self):
        return None

    def handle_event(self, event):
        return None

    def update(self, now):
        return None

    def draw(self, screen):
        return None

    def confirm(self):
        return False

    def start_success_animation(self):
        return False

    def animation_finished(self, now):
        return True

    def record_result(self, success):
        if success:
            self.success_count += 1
            self.streak += 1
            self.best_streak = max(self.best_streak, self.streak)
        else:
            self.fail_count += 1
            self.streak = 0

    def metric_display(self):
        total = self.success_count + self.fail_count
        if total <= 0:
            return "-"
        return f"{round(self.success_count / total * 100)}%"

    def training_metrics(self):
        total = self.success_count + self.fail_count
        accuracy = round(self.success_count / total * 100, 1) if total else 0.0
        return {"fusion_accuracy": accuracy, "best_streak": self.best_streak}

    def reward_summary(self):
        if self.best_streak >= 5:
            return self.scene.manager.t("fusion_common.reward.super")
        if self.best_streak >= 3:
            return self.scene.manager.t("fusion_common.reward.good")
        return self.scene.manager.t("fusion_common.reward.try")

    def next_goal_text(self):
        return self.scene.manager.t("fusion_common.next_goal")

    def goal_label(self):
        mapping = {
            "puzzle_fusion": "fusion_common.goal.align",
            "bridge_fusion": "fusion_common.goal.cross",
            "rail_fusion": "fusion_common.goal.rail",
        }
        return self.scene.manager.t(mapping.get(self.scene.config.mechanic_type, "fusion_common.goal.align"))

    def stage_label(self):
        progress = self.scene.session_progress()
        if progress < 0.34:
            return self.scene.manager.t("fusion_common.stage.warmup")
        if progress < 0.67:
            return self.scene.manager.t("fusion_common.stage.steady")
        return self.scene.manager.t("fusion_common.stage.challenge")


class _PuzzleFusionMechanic(_FusionMechanic):
    SHAPES = ("fish", "star", "apple", "butterfly")

    def __init__(self, scene):
        super().__init__(scene)
        self.offset = 0
        self.target_shape = "fish"
        self.base_color = (255, 220, 120, 255)
        self.shape_surface = pygame.Surface((160, 160), pygame.SRCALPHA)

    def start_task(self):
        progress = self.scene.session_progress()
        if progress < 0.34:
            self.offset = random.choice([-32, -20, 20, 32])
        elif progress < 0.67:
            self.offset = random.choice([-44, -30, -16, 16, 30, 44])
        else:
            self.offset = random.choice([-56, -44, -30, -18, 18, 30, 44, 56])
        self.target_shape = random.choice(self.SHAPES)
        self.base_color = random.choice(((255, 220, 120, 255), (160, 224, 255, 255), (255, 160, 160, 255)))
        self.shape_surface = self._build_shape(self.target_shape, self.base_color)

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_LEFT:
                self.offset = max(-60, self.offset - 7)
            elif event.key == pygame.K_RIGHT:
                self.offset = min(60, self.offset + 7)

    def confirm(self):
        progress = self.scene.session_progress()
        tolerance = 10 if progress < 0.34 else 8 if progress < 0.67 else 6
        return abs(self.offset) <= tolerance

    def draw(self, screen):
        cx, cy = self.scene.play_area.centerx, self.scene.play_area.centery + 10
        left_half = pygame.Surface(self.shape_surface.get_size(), pygame.SRCALPHA)
        right_half = pygame.Surface(self.shape_surface.get_size(), pygame.SRCALPHA)
        mid_x = self.shape_surface.get_width() // 2
        left_half.blit(self.shape_surface, (0, 0), pygame.Rect(0, 0, mid_x, self.shape_surface.get_height()))
        right_half.blit(self.shape_surface, (0, 0), pygame.Rect(mid_x, 0, self.shape_surface.get_width() - mid_x, self.shape_surface.get_height()))
        self.scene.draw_binocular_pair(screen, left_half, right_half, (cx, cy), left_offset=(-self.offset // 2, 0), right_offset=(self.offset // 2, 0))
        label = self.scene.body_font.render(self.scene.manager.t("fusion_common.puzzle_label"), True, (58, 70, 102))
        screen.blit(label, (cx - label.get_width() // 2, self.scene.play_area.bottom - 42))

    def training_metrics(self):
        total = self.success_count + self.fail_count
        accuracy = round(self.success_count / total * 100, 1) if total else 0.0
        return {"puzzle_fusion_accuracy": accuracy, "best_streak": self.best_streak}

    def reward_summary(self):
        if self.best_streak >= 5:
            return self.scene.manager.t("puzzle_fusion.reward.super")
        if self.best_streak >= 3:
            return self.scene.manager.t("puzzle_fusion.reward.good")
        return self.scene.manager.t("puzzle_fusion.reward.try")

    def next_goal_text(self):
        return self.scene.manager.t("puzzle_fusion.next_goal")

    def _build_shape(self, shape_id, color):
        surf = pygame.Surface((220, 220), pygame.SRCALPHA)
        cx, cy = 110, 110
        if shape_id == "fish":
            pygame.draw.ellipse(surf, color, pygame.Rect(cx - 62, cy - 34, 112, 68))
            pygame.draw.polygon(surf, color, [(cx + 44, cy), (cx + 84, cy - 30), (cx + 84, cy + 30)])
        elif shape_id == "star":
            points = []
            for i in range(10):
                angle = -math.pi / 2 + i * math.pi / 5
                radius = 62 if i % 2 == 0 else 28
                points.append((cx + int(math.cos(angle) * radius), cy + int(math.sin(angle) * radius)))
            pygame.draw.polygon(surf, color, points)
        elif shape_id == "apple":
            pygame.draw.circle(surf, color, (cx - 20, cy + 10), 40)
            pygame.draw.circle(surf, color, (cx + 20, cy + 10), 40)
            pygame.draw.polygon(surf, color, [(cx - 58, cy), (cx, cy - 52), (cx + 58, cy), (cx + 34, cy + 56), (cx - 34, cy + 56)])
        else:
            pygame.draw.ellipse(surf, color, pygame.Rect(cx - 78, cy - 48, 62, 76))
            pygame.draw.ellipse(surf, color, pygame.Rect(cx + 16, cy - 48, 62, 76))
            pygame.draw.ellipse(surf, color, pygame.Rect(cx - 70, cy + 8, 56, 66))
            pygame.draw.ellipse(surf, color, pygame.Rect(cx + 14, cy + 8, 56, 66))
            pygame.draw.rect(surf, (60, 60, 72, 255), pygame.Rect(cx - 7, cy - 34, 14, 100), border_radius=8)
        return surf


class _BridgeFusionMechanic(_FusionMechanic):
    def __init__(self, scene):
        super().__init__(scene)
        self.offset = 0
        self.crossing_started_at = 0.0
        self.crossing_duration = 1.1
        self.bridge_glow_until = 0.0

    def start_task(self):
        progress = self.scene.session_progress()
        if progress < 0.34:
            self.offset = random.choice([-20, -12, 12, 20])
        elif progress < 0.67:
            self.offset = random.choice([-36, -24, -12, 12, 24, 36])
        else:
            self.offset = random.choice([-48, -36, -24, -12, 12, 24, 36, 48])

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_LEFT:
                self.offset = max(-50, self.offset - 6)
            elif event.key == pygame.K_RIGHT:
                self.offset = min(50, self.offset + 6)

    def confirm(self):
        progress = self.scene.session_progress()
        tolerance = 12 if progress < 0.34 else 10 if progress < 0.67 else 7
        return abs(self.offset) <= tolerance

    def draw(self, screen):
        cx = self.scene.play_area.centerx
        cy = self.scene.play_area.centery + 8
        water = pygame.Rect(self.scene.play_area.left + 90, cy - 34, self.scene.play_area.width - 180, 84)
        pygame.draw.rect(screen, (120, 190, 246), water, border_radius=18)
        pygame.draw.rect(screen, (234, 208, 164), pygame.Rect(water.left - 40, cy - 50, 52, 116), border_radius=18)
        pygame.draw.rect(screen, (234, 208, 164), pygame.Rect(water.right - 12, cy - 50, 52, 116), border_radius=18)

        left_bridge = pygame.Surface((300, 92), pygame.SRCALPHA)
        right_bridge = pygame.Surface((300, 92), pygame.SRCALPHA)
        for i in range(4):
            pygame.draw.rect(left_bridge, (212, 158, 104, 255), pygame.Rect(i * 60, 24, 48, 32), border_radius=8)
            pygame.draw.rect(right_bridge, (212, 158, 104, 255), pygame.Rect(i * 60, 24, 48, 32), border_radius=8)
        self.scene.draw_binocular_pair(
            screen,
            left_bridge,
            right_bridge,
            (cx, cy),
            left_offset=(-self.offset // 2, 0),
            right_offset=(self.offset // 2, 0),
        )
        if self.bridge_glow_until and time.time() <= self.bridge_glow_until:
            glow = pygame.Surface((water.width - 56, 44), pygame.SRCALPHA)
            glow.fill((255, 244, 168, 88))
            screen.blit(glow, (water.x + 28, cy - 2))
        if self.crossing_started_at:
            progress = min(1.0, max(0.0, (time.time() - self.crossing_started_at) / self.crossing_duration))
            player_x = int((water.left + 8) * (1 - progress) + (water.right - 8) * progress)
        else:
            player_x = water.left - 12 if abs(self.offset) > 10 else water.left + 8
        shadow = pygame.Surface((54, 24), pygame.SRCALPHA)
        pygame.draw.ellipse(shadow, (40, 50, 70, 60), shadow.get_rect())
        screen.blit(shadow, (player_x - 27, cy + 28))
        pygame.draw.circle(screen, (255, 214, 120), (player_x, cy + 28), 22)
        pygame.draw.circle(screen, (255, 246, 208), (player_x - 8, cy + 20), 6)
        label = self.scene.body_font.render(self.scene.manager.t("fusion_common.bridge_label"), True, (58, 70, 102))
        screen.blit(label, (cx - label.get_width() // 2, self.scene.play_area.bottom - 42))

    def training_metrics(self):
        total = self.success_count + self.fail_count
        accuracy = round(self.success_count / total * 100, 1) if total else 0.0
        return {"bridge_fusion_accuracy": accuracy, "best_streak": self.best_streak}

    def reward_summary(self):
        if self.best_streak >= 5:
            return self.scene.manager.t("bridge_fusion.reward.super")
        if self.best_streak >= 3:
            return self.scene.manager.t("bridge_fusion.reward.good")
        return self.scene.manager.t("bridge_fusion.reward.try")

    def next_goal_text(self):
        return self.scene.manager.t("bridge_fusion.next_goal")

    def start_success_animation(self):
        self.crossing_started_at = time.time()
        self.bridge_glow_until = self.crossing_started_at + self.crossing_duration
        return True

    def animation_finished(self, now):
        return self.crossing_started_at > 0 and (now - self.crossing_started_at) >= self.crossing_duration


class _RailFusionMechanic(_FusionMechanic):
    def __init__(self, scene):
        super().__init__(scene)
        self.current_state = 0
        self.correct_state = 0
        self.state_count = 3
        self.train_departed_at = 0.0
        self.train_duration = 1.2

    def start_task(self):
        max_state = 2 if self.scene.session_progress() < 0.5 else 3
        self.state_count = max_state + 1
        self.current_state = random.randint(0, max_state)
        self.correct_state = random.randint(0, max_state)

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_LEFT:
                self.current_state = (self.current_state - 1) % self.state_count
            elif event.key == pygame.K_RIGHT:
                self.current_state = (self.current_state + 1) % self.state_count

    def confirm(self):
        return self.current_state == self.correct_state

    def draw(self, screen):
        cx = self.scene.play_area.centerx
        cy = self.scene.play_area.centery + 10
        start = (self.scene.play_area.left + 90, cy)
        end = (self.scene.play_area.right - 90, cy)
        pygame.draw.line(screen, (96, 110, 144), (start[0], cy), (start[0] + 80, cy), 10)
        pygame.draw.line(screen, (96, 110, 144), (end[0] - 80, cy), (end[0], cy), 10)

        left_track = pygame.Surface((260, 160), pygame.SRCALPHA)
        right_track = pygame.Surface((260, 160), pygame.SRCALPHA)
        self._draw_track_half(left_track, "left", self.current_state)
        self._draw_track_half(right_track, "right", self.correct_state)
        self.scene.draw_binocular_pair(screen, left_track, right_track, (cx, cy))

        if self.train_departed_at:
            progress = min(1.0, max(0.0, (time.time() - self.train_departed_at) / self.train_duration))
            train_x = int((start[0] + 18) * (1 - progress) + (end[0] - 70) * progress)
        else:
            train_x = start[0] + 18
        glow = pygame.Surface((76, 22), pygame.SRCALPHA)
        pygame.draw.ellipse(glow, (36, 46, 66, 58), glow.get_rect())
        screen.blit(glow, (train_x - 8, cy + 18))
        pygame.draw.rect(screen, (240, 108, 88), pygame.Rect(train_x, cy - 24, 60, 38), border_radius=10)
        pygame.draw.rect(screen, (255, 228, 210), pygame.Rect(train_x + 34, cy - 16, 14, 10), border_radius=4)
        pygame.draw.circle(screen, (52, 60, 82), (train_x + 14, cy + 18), 8)
        pygame.draw.circle(screen, (52, 60, 82), (train_x + 46, cy + 18), 8)
        label = self.scene.body_font.render(self.scene.manager.t("fusion_common.rail_label"), True, (58, 70, 102))
        screen.blit(label, (cx - label.get_width() // 2, self.scene.play_area.bottom - 42))

    def training_metrics(self):
        total = self.success_count + self.fail_count
        accuracy = round(self.success_count / total * 100, 1) if total else 0.0
        return {"rail_fusion_accuracy": accuracy, "best_streak": self.best_streak}

    def reward_summary(self):
        if self.best_streak >= 5:
            return self.scene.manager.t("rail_fusion.reward.super")
        if self.best_streak >= 3:
            return self.scene.manager.t("rail_fusion.reward.good")
        return self.scene.manager.t("rail_fusion.reward.try")

    def next_goal_text(self):
        return self.scene.manager.t("rail_fusion.next_goal")

    def start_success_animation(self):
        self.train_departed_at = time.time()
        return True

    def animation_finished(self, now):
        return self.train_departed_at > 0 and (now - self.train_departed_at) >= self.train_duration

    def _draw_track_half(self, surface, side, state):
        color = (124, 136, 176, 255)
        x_mid = surface.get_width() // 2
        y_map = {0: 80, 1: 30, 2: 130, 3: 56}
        if side == "left":
            pygame.draw.line(surface, color, (0, 80), (x_mid, y_map[state]), 14)
        else:
            pygame.draw.line(surface, color, (x_mid, y_map[state]), (surface.get_width(), 80), 14)


class FusionTrainingScene(BaseScene):
    STATE_HOME = "home"
    STATE_HELP = "help"
    STATE_PLAY = "play"
    STATE_RESULT = "result"

    MODE_NAKED = "naked"
    MODE_GLASSES = MODE_GLASSES
    FILTER_LR = FILTER_LR
    FILTER_RL = FILTER_RL

    def __init__(self, manager, config: FusionGameConfig):
        super().__init__(manager)
        self.config = config
        self.width, self.height = 900, 700
        self.state = self.STATE_HOME
        self.mode = self.MODE_NAKED
        self.filter_direction = self.FILTER_LR
        self.show_filter_picker = False
        self.selected_index = 0
        self.result_selected = 0
        self.session_started_at = 0.0
        self.score = 0
        self.correct_count = 0
        self.wrong_count = 0
        self.feedback_text = ""
        self.feedback_color = (255, 255, 255)
        self.feedback_until = 0.0
        self.final_stats = {}
        self.pending_next_task = False
        self._refresh_fonts()
        self._build_ui_rects()
        self.mechanic = self._create_mechanic()
        self.mechanic.start_task()

    def _refresh_fonts(self):
        self.title_font = self.create_font(54)
        self.sub_font = self.create_font(24)
        self.option_font = self.create_font(28)
        self.body_font = self.create_font(22)
        self.small_font = self.create_font(18)

    def _build_ui_rects(self):
        card_w = min(560, self.width - 120)
        card_h = 60
        start_x = self.width // 2 - card_w // 2
        start_y = 224
        gap = 16
        self.btn_start = pygame.Rect(start_x, start_y, card_w, card_h)
        self.btn_glasses = pygame.Rect(start_x, start_y + card_h + gap, card_w, card_h)
        self.btn_help = pygame.Rect(start_x, start_y + (card_h + gap) * 2, card_w, card_h)
        self.btn_back = pygame.Rect(self.width - 108, 18, 88, 36)
        self.btn_home = pygame.Rect(self.width - 108, 18, 88, 36)
        self.btn_confirm = pygame.Rect(self.width // 2 - 94, self.height - 62, 188, 44)
        self.btn_continue = pygame.Rect(self.width // 2 - 210, self.height - 98, 180, 48)
        self.btn_exit = pygame.Rect(self.width // 2 + 30, self.height - 98, 180, 48)
        self.help_ok = pygame.Rect(self.width // 2 - 90, self.height - 90, 180, 54)
        self.filter_modal = pygame.Rect(self.width // 2 - 250, self.height // 2 - 128, 500, 220)
        self.filter_lr = pygame.Rect(self.filter_modal.x + 24, self.filter_modal.y + 68, 210, 46)
        self.filter_rl = pygame.Rect(self.filter_modal.x + 266, self.filter_modal.y + 68, 210, 46)
        self.filter_start = pygame.Rect(self.filter_modal.centerx - 90, self.filter_modal.y + 150, 180, 44)
        self.play_area = pygame.Rect(92, 118, self.width - 184, self.height - 260)

    def on_resize(self, width, height):
        self.width, self.height = width, height
        self._build_ui_rects()

    def reset(self):
        self.state = self.STATE_HOME
        self.mode = self.MODE_NAKED
        self.filter_direction = self.FILTER_LR
        self.show_filter_picker = False
        self.selected_index = 0
        self.result_selected = 0
        self.score = 0
        self.correct_count = 0
        self.wrong_count = 0
        self.feedback_text = ""
        self.pending_next_task = False
        self.mechanic = self._create_mechanic()
        self.mechanic.start_task()

    def _create_mechanic(self):
        if self.config.mechanic_type == "puzzle_fusion":
            return _PuzzleFusionMechanic(self)
        if self.config.mechanic_type == "bridge_fusion":
            return _BridgeFusionMechanic(self)
        return _RailFusionMechanic(self)

    def _session_seconds(self):
        try:
            minutes = int(self.manager.settings.get("session_duration_minutes", 5))
        except (TypeError, ValueError):
            minutes = 5
        return max(60, minutes * 60)

    def _start_session(self):
        self.state = self.STATE_PLAY
        self.score = 0
        self.correct_count = 0
        self.wrong_count = 0
        self.feedback_text = ""
        self.pending_next_task = False
        self.session_started_at = time.time()
        self.mechanic = self._create_mechanic()
        self.mechanic.start_task()

    def _finish_session(self):
        duration = min(self._session_seconds(), max(0.0, time.time() - self.session_started_at))
        total = self.correct_count + self.wrong_count
        accuracy = round(self.correct_count / total * 100, 1) if total else 0.0
        stars = 3 if accuracy >= 85 else 2 if accuracy >= 60 else 1 if total else 0
        self.final_stats = {
            "duration": int(duration),
            "score": self.score,
            "correct": self.correct_count,
            "accuracy_rate": accuracy,
            "reward_summary": self.mechanic.reward_summary(),
            "next_goal": self.mechanic.next_goal_text(),
            "stars": stars,
            "mode": self.mode,
            "filter_direction": self.filter_direction,
        }
        payload = {
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
            "game_id": self.config.game_id,
            "difficulty_level": 1,
            "total_questions": total,
            "correct_count": self.correct_count,
            "wrong_count": self.wrong_count,
            "duration_seconds": duration,
            "accuracy_rate": accuracy,
            "training_metrics": self.mechanic.training_metrics(),
        }
        self.manager.current_result = {"correct": self.correct_count, "total": total, "game_id": self.config.game_id}
        self.manager.data_manager.save_training_session(payload)
        if hasattr(self.manager, "sound_manager"):
            self.manager.sound_manager.play_completed()
        self.state = self.STATE_RESULT
        self.result_selected = 0

    def _set_feedback(self, key, color, extra=""):
        self.feedback_text = self.manager.t(key)
        if extra:
            self.feedback_text = f"{self.feedback_text} {extra}"
        self.feedback_color = color
        self.feedback_until = time.time() + 1.0

    def session_progress(self):
        if not self.session_started_at:
            return 0.0
        return min(1.0, max(0.0, (time.time() - self.session_started_at) / self._session_seconds()))

    def draw_binocular_pair(self, screen, left_surface, right_surface, center, left_offset=(0, 0), right_offset=(0, 0)):
        left = apply_filter(left_surface, self.mode, self.filter_direction, "left")
        right = apply_filter(right_surface, self.mode, self.filter_direction, "right")
        blend_layer = blend_filtered_patterns(
            (self.width, self.height),
            left,
            left.get_rect(center=(center[0] + left_offset[0], center[1] + left_offset[1])),
            right,
            right.get_rect(center=(center[0] + right_offset[0], center[1] + right_offset[1])),
        )
        screen.blit(blend_layer, (0, 0))

    def _draw_gradient_bg(self, screen):
        top = (232, 242, 255)
        bottom = (214, 235, 252)
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

    def _draw_button(self, screen, rect, text, color, text_color=(255, 255, 255), selected=False):
        if selected:
            pygame.draw.rect(screen, (255, 246, 194), rect.inflate(10, 10), border_radius=14)
        pygame.draw.rect(screen, color, rect, border_radius=12)
        pygame.draw.rect(screen, (255, 255, 255), rect, 2, border_radius=12)
        surface = self.option_font.render(text, True, text_color)
        screen.blit(surface, (rect.centerx - surface.get_width() // 2, rect.centery - surface.get_height() // 2))
        if selected:
            pygame.draw.circle(screen, (255, 255, 255), (rect.right - 18, rect.centery), 8)
            pygame.draw.circle(screen, (218, 102, 68), (rect.right - 18, rect.centery), 3)

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

    def _format_time(self, sec):
        s = max(0, int(sec))
        return f"{s // 60:02d}:{s % 60:02d}"

    def handle_events(self, events):
        for event in events:
            if self.state == self.STATE_HOME:
                if event.type == pygame.KEYDOWN:
                    if self.show_filter_picker:
                        if event.key == pygame.K_LEFT:
                            self.filter_direction = self.FILTER_LR
                        elif event.key == pygame.K_RIGHT:
                            self.filter_direction = self.FILTER_RL
                        elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
                            self.show_filter_picker = False
                            self._start_session()
                        elif event.key == pygame.K_ESCAPE:
                            self.show_filter_picker = False
                        continue
                    if event.key == pygame.K_ESCAPE:
                        self.manager.set_scene("category")
                    elif event.key in (pygame.K_UP, pygame.K_DOWN):
                        self.selected_index = (self.selected_index + (-1 if event.key == pygame.K_UP else 1)) % 3
                    elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
                        if self.selected_index == 0:
                            self.mode = self.MODE_NAKED
                            self._start_session()
                        elif self.selected_index == 1:
                            self.mode = self.MODE_GLASSES
                            self.show_filter_picker = True
                        else:
                            self.state = self.STATE_HELP
                elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    pos = event.pos
                    if self.show_filter_picker:
                        if self.filter_lr.collidepoint(pos):
                            self.filter_direction = self.FILTER_LR
                        elif self.filter_rl.collidepoint(pos):
                            self.filter_direction = self.FILTER_RL
                        elif self.filter_start.collidepoint(pos):
                            self.show_filter_picker = False
                            self._start_session()
                        continue
                    if self.btn_back.collidepoint(pos):
                        self.manager.set_scene("category")
                    elif self.btn_start.collidepoint(pos):
                        self.mode = self.MODE_NAKED
                        self._start_session()
                    elif self.btn_glasses.collidepoint(pos):
                        self.mode = self.MODE_GLASSES
                        self.show_filter_picker = True
                    elif self.btn_help.collidepoint(pos):
                        self.state = self.STATE_HELP
            elif self.state == self.STATE_HELP:
                if event.type == pygame.KEYDOWN and event.key in (pygame.K_ESCAPE, pygame.K_RETURN, pygame.K_SPACE):
                    self.state = self.STATE_HOME
                elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1 and self.help_ok.collidepoint(event.pos):
                    self.state = self.STATE_HOME
            elif self.state == self.STATE_PLAY:
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        self.manager.set_scene("category")
                    elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
                        self._confirm_action()
                    else:
                        self.mechanic.handle_event(event)
                elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    if self.btn_home.collidepoint(event.pos):
                        self.manager.set_scene("category")
                    elif self.btn_confirm.collidepoint(event.pos):
                        self._confirm_action()
            else:
                if event.type == pygame.KEYDOWN:
                    if event.key in (pygame.K_LEFT, pygame.K_RIGHT):
                        self.result_selected = 1 - self.result_selected
                    elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
                        if self.result_selected == 0:
                            self.state = self.STATE_HOME
                        else:
                            self.manager.set_scene("category")
                    elif event.key == pygame.K_ESCAPE:
                        self.manager.set_scene("category")
                elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    if self.btn_continue.collidepoint(event.pos):
                        self.state = self.STATE_HOME
                    elif self.btn_exit.collidepoint(event.pos):
                        self.manager.set_scene("category")

    def _confirm_action(self):
        success = bool(self.mechanic.confirm())
        self.mechanic.record_result(success)
        if success:
            self.correct_count += 1
            gained = 10 + max(0, self.mechanic.streak - 1) * 2
            self.score += gained
            if hasattr(self.manager, "sound_manager"):
                self.manager.sound_manager.play_correct()
            self._set_feedback("fusion_common.success", (90, 202, 120), f"+{gained}")
            self.pending_next_task = self.mechanic.start_success_animation()
        else:
            self.wrong_count += 1
            if hasattr(self.manager, "sound_manager"):
                self.manager.sound_manager.play_wrong()
            self._set_feedback("fusion_common.fail", (228, 108, 108))
            self.pending_next_task = False
        if not self.pending_next_task:
            self.mechanic.start_task()

    def update(self):
        if self.state == self.STATE_PLAY and self.session_started_at:
            self.mechanic.update(time.time())
            if time.time() - self.session_started_at >= self._session_seconds():
                self._finish_session()
                return
            if self.pending_next_task and self.mechanic.animation_finished(time.time()):
                self.pending_next_task = False
                self.mechanic.start_task()
        if self.feedback_text and time.time() > self.feedback_until:
            self.feedback_text = ""

    def _draw_help_step(self, screen, idx, y, text):
        x = 120
        pygame.draw.circle(screen, (122, 154, 212), (x + 18, y + 16), 16)
        num = self.small_font.render(str(idx), True, (255, 255, 255))
        screen.blit(num, (x + 18 - num.get_width() // 2, y + 16 - num.get_height() // 2))
        step = self.small_font.render(text, True, (58, 84, 118))
        screen.blit(step, (x + 48, y + 6))

    def _draw_home(self, screen):
        title = self.title_font.render(self.manager.t(self.config.title_key), True, (40, 66, 108))
        subtitle = self.sub_font.render(self.manager.t(self.config.subtitle_key), True, (92, 114, 146))
        screen.blit(title, (self.width // 2 - title.get_width() // 2, 84))
        screen.blit(subtitle, (self.width // 2 - subtitle.get_width() // 2, 146))
        self._draw_button(screen, self.btn_start, self.manager.t("fusion_common.home.start"), self.config.theme_color, selected=self.selected_index == 0)
        self._draw_button(screen, self.btn_glasses, self.manager.t("fusion_common.home.glasses"), (94, 126, 216), selected=self.selected_index == 1)
        self._draw_button(screen, self.btn_help, self.manager.t("fusion_common.home.help"), (126, 142, 174), selected=self.selected_index == 2)
        self._draw_button(screen, self.btn_back, self.manager.t("common.back"), (86, 116, 170))
        if self.show_filter_picker:
            modal = pygame.Surface((self.filter_modal.width, self.filter_modal.height), pygame.SRCALPHA)
            modal.fill((248, 253, 255, 238))
            screen.blit(modal, self.filter_modal.topleft)
            pygame.draw.rect(screen, (116, 148, 196), self.filter_modal, 2, border_radius=12)
            msg = self.body_font.render(self.manager.t("fusion_common.filter.pick"), True, (52, 76, 110))
            screen.blit(msg, (self.filter_modal.centerx - msg.get_width() // 2, self.filter_modal.y + 24))
            self._draw_filter_option(screen, self.filter_lr, self.manager.t("fusion_common.filter.lr"), RED_FILTER[:3], BLUE_FILTER[:3], self.filter_direction == self.FILTER_LR)
            self._draw_filter_option(screen, self.filter_rl, self.manager.t("fusion_common.filter.rl"), BLUE_FILTER[:3], RED_FILTER[:3], self.filter_direction == self.FILTER_RL)
            self._draw_button(screen, self.filter_start, self.manager.t("fusion_common.filter.start"), (86, 150, 108))

    def _draw_help(self, screen):
        title = self.title_font.render(self.manager.t("fusion_common.help.title"), True, (42, 70, 110))
        screen.blit(title, (self.width // 2 - title.get_width() // 2, 76))
        for idx, key in enumerate(self.config.help_steps, start=1):
            self._draw_help_step(screen, idx, 190 + (idx - 1) * 90, self.manager.t(key))
        self._draw_button(screen, self.help_ok, self.manager.t("fusion_common.help.ok"), (242, 214, 126), text_color=(104, 84, 42))

    def _draw_play(self, screen):
        hud_primary = (42, 12, 72) if self.mode == self.MODE_GLASSES else (55, 82, 122)
        guide = self.small_font.render(self.manager.t(self.config.guide_key), True, hud_primary)
        screen.blit(guide, (self.play_area.centerx - guide.get_width() // 2, self.play_area.top + 16))
        remaining = max(0, self._session_seconds() - (time.time() - self.session_started_at))
        timer = self.body_font.render(self.manager.t("fusion_common.time", sec=self._format_time(remaining)), True, hud_primary)
        score = self.body_font.render(self.manager.t("fusion_common.score", score=self.score), True, hud_primary)
        screen.blit(timer, (self.width // 2 - timer.get_width() // 2, 14))
        screen.blit(score, (self.width // 2 - score.get_width() // 2, 42))
        stage = self.small_font.render(self.mechanic.stage_label(), True, (94, 110, 150))
        screen.blit(stage, (24, 18))
        if self.mode == self.MODE_GLASSES:
            direction_key = "fusion_common.filter.lr" if self.filter_direction == self.FILTER_LR else "fusion_common.filter.rl"
            direction = self.small_font.render(self.manager.t(direction_key), True, (72, 28, 104))
            screen.blit(direction, (24, 42))
        if self.mechanic.streak > 1:
            streak = self.small_font.render(self.manager.t("fusion_common.streak", n=self.mechanic.streak), True, (214, 104, 72))
            screen.blit(streak, (self.width - streak.get_width() - 24, 18))
        goal = self.small_font.render(self.mechanic.goal_label(), True, (94, 110, 150))
        screen.blit(goal, (self.play_area.centerx - goal.get_width() // 2, self.play_area.top + 46))
        self.mechanic.draw(screen)
        self._draw_button(screen, self.btn_confirm, self.manager.t("fusion_common.confirm"), (82, 146, 108))
        self._draw_button(screen, self.btn_home, self.manager.t("common.back"), (86, 116, 170))
        if self.feedback_text:
            fb = self.body_font.render(self.feedback_text, True, self.feedback_color)
            screen.blit(fb, (self.width // 2 - fb.get_width() // 2, self.play_area.top + 84))

    def _draw_result(self, screen):
        title = self.title_font.render(self.manager.t("fusion_common.result.title"), True, (42, 70, 110))
        screen.blit(title, (self.width // 2 - title.get_width() // 2, 100))
        lines = [
            self.manager.t("fusion_common.result.score", n=self.final_stats.get("score", 0)),
            self.manager.t("fusion_common.result.success", n=self.final_stats.get("correct", 0)),
            self.manager.t(
                "fusion_common.result.mode",
                text=self.manager.t("fusion_common.home.glasses")
                if self.final_stats.get("mode") == self.MODE_GLASSES
                else self.manager.t("fusion_common.home.start"),
            ),
            self.manager.t("fusion_common.result.reward", text=self.final_stats.get("reward_summary", "")),
            self.manager.t("fusion_common.result.next", text=self.final_stats.get("next_goal", "")),
        ]
        for idx, text in enumerate(lines):
            line = self.body_font.render(text, True, (58, 84, 118))
            screen.blit(line, (self.width // 2 - line.get_width() // 2, 192 + idx * 40))
        self._draw_button(screen, self.btn_continue, self.manager.t("fusion_common.result.continue"), (84, 148, 108), selected=self.result_selected == 0)
        self._draw_button(screen, self.btn_exit, self.manager.t("fusion_common.result.exit"), (120, 134, 168), selected=self.result_selected == 1)

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
