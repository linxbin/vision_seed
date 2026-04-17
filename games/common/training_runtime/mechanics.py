import math
import random
import time
from dataclasses import dataclass
from datetime import datetime

import pygame

from core.asset_loader import load_image_if_exists, project_path


class BaseArcadeMechanic:
    def __init__(self, scene):
        self.scene = scene
        self.outcome = None

    def start_round(self):
        self.outcome = None

    def handle_event(self, event):
        return None

    def update(self, now):
        return None

    def draw(self, screen):
        return None

    def _resolve(self, success):
        if self.outcome is None:
            self.outcome = bool(success)

    def consume_outcome(self):
        outcome = self.outcome
        self.outcome = None
        return outcome

    def training_metrics(self, scene):
        return {}

    def metric_display(self, scene):
        return "-"

    def score_for_outcome(self, success):
        return 10 if success else 0

    def feedback_for_outcome(self, scene, success):
        return ("arcade.play.correct", (86, 174, 112)) if success else ("arcade.play.wrong", (224, 110, 110))

    def stage_label(self, scene):
        return "-"

    def goal_label(self, scene):
        return "-"

    def reward_summary(self, scene):
        return ""

    def next_goal_text(self, scene):
        return ""


class CatchFruitMechanic(BaseArcadeMechanic):
    def __init__(self, scene):
        super().__init__(scene)
        self.basket_x = 0
        self.move_dir = 0
        self.move_speed = 8
        self.fruit_x = 0
        self.fruit_y = 0
        self.fruit_speed = 0
        self.start_size = 88
        self.end_size = 36
        self.clear_hits = 0
        self.smallest_caught = None
        self.catch_window_top = 0
        self.space_prompt = False
        self.streak = 0
        self.best_streak = 0
        self.bonus_hits = 0
        self.last_success_bonus = False
        self.fruit_asset_name = "apple"
        self.fruit_assets = {
            name: project_path("games", "accommodation", "catch_fruit", "assets", "objects", f"{name}.png")
            for name in ("apple", "banana", "orange", "strawberry", "grapes", "watermelon")
        }
        self.basket_asset = project_path("games", "accommodation", "catch_fruit", "assets", "objects", "basket.png")
        self.fruit_points = {"apple": 10, "banana": 10, "orange": 10, "strawberry": 12, "grapes": 12, "watermelon": 18}

    def start_round(self):
        super().start_round()
        self.basket_x = self.scene.play_area.centerx
        self.fruit_x = random.randint(self.scene.play_area.left + 60, self.scene.play_area.right - 60)
        self.fruit_y = self.scene.play_area.top + 24
        self.fruit_speed = random.uniform(3.2, 4.8) + self.scene.config.difficulty_level * 0.25
        self.catch_window_top = self.scene.play_area.bottom - 118
        stage = self._stage_index()
        if stage == 0:
            self.fruit_speed -= 0.4
            self.fruit_asset_name = random.choice(("apple", "banana", "orange"))
        elif stage == 1:
            self.fruit_speed += 0.2
            self.fruit_asset_name = random.choice(("apple", "orange", "strawberry", "grapes"))
        else:
            self.fruit_speed += 0.8
            self.fruit_asset_name = random.choice(tuple(self.fruit_assets.keys()))
        self.last_success_bonus = False

    def handle_event(self, event):
        if event.type == pygame.MOUSEMOTION:
            self.basket_x = max(self.scene.play_area.left + 60, min(self.scene.play_area.right - 60, event.pos[0]))
        elif event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_LEFT, pygame.K_a):
                self.move_dir = -1
            elif event.key in (pygame.K_RIGHT, pygame.K_d):
                self.move_dir = 1
            elif event.key == pygame.K_SPACE:
                self._resolve(True)
        elif event.type == pygame.KEYUP and event.key in (pygame.K_LEFT, pygame.K_a, pygame.K_RIGHT, pygame.K_d):
            self.move_dir = 0

    def update(self, now):
        frame_scale = self.scene.frame_scale()
        self.basket_x = max(self.scene.play_area.left + 60, min(self.scene.play_area.right - 60, self.basket_x + self.move_dir * self.move_speed * frame_scale))
        self.fruit_y += self.fruit_speed * frame_scale
        if self.fruit_y >= self.catch_window_top:
            if abs(self.fruit_x - self.basket_x) < 48:
                self.streak += 1
                self.best_streak = max(self.best_streak, self.streak)
                self.clear_hits += 1
                points = self.fruit_points.get(self.fruit_asset_name, 10)
                if points >= 12:
                    self.bonus_hits += 1
                self.smallest_caught = min(self.smallest_caught or points, points)
                self.last_success_bonus = points >= 12
                self.scene.score += points
                self._resolve(True)
            else:
                self.streak = 0
                self._resolve(False)
            return True
        return None

    def draw(self, screen):
        fruit_img = load_image_if_exists(self.fruit_assets.get(self.fruit_asset_name))
        size = max(self.end_size, int(self.start_size - (self.start_size - self.end_size) * ((self.fruit_y - self.scene.play_area.top) / max(1, self.catch_window_top - self.scene.play_area.top))))
        if fruit_img:
            fruit_img = pygame.transform.smoothscale(fruit_img, (size, size))
            screen.blit(fruit_img, (int(self.fruit_x - size // 2), int(self.fruit_y - size // 2)))
        else:
            pygame.draw.circle(screen, (220, 80, 80), (int(self.fruit_x), int(self.fruit_y)), size // 2)
        basket_img = load_image_if_exists(self.basket_asset)
        if basket_img:
            basket_img = pygame.transform.smoothscale(basket_img, (96, 48))
            screen.blit(basket_img, (int(self.basket_x - 48), int(self.scene.play_area.bottom - 48)))
        else:
            pygame.draw.rect(screen, (139, 90, 43), (int(self.basket_x - 48), int(self.scene.play_area.bottom - 48), 96, 48), border_radius=6)

    def training_metrics(self, scene):
        return {"best_streak": self.best_streak, "clear_hits": self.clear_hits, "bonus_hits": self.bonus_hits}

    def metric_display(self, scene):
        return str(self.clear_hits)

    def score_for_outcome(self, success):
        if not success:
            return 0
        score = self.fruit_points.get(self.fruit_asset_name, 10)
        if self.streak >= 3:
            score += 8
        if self.last_success_bonus:
            score += 12
        return score

    def feedback_for_outcome(self, scene, success):
        if not success:
            return ("catch_fruit.feedback.miss", (214, 96, 96))
        if self.last_success_bonus:
            return ("catch_fruit.feedback.bonus", (88, 162, 108))
        if self.streak >= 3:
            return ("catch_fruit.feedback.combo", (92, 156, 222))
        return ("arcade.play.correct", (86, 174, 112))

    def stage_label(self, scene):
        return scene.manager.t(("catch_fruit.stage.warmup", "catch_fruit.stage.steady", "catch_fruit.stage.sprint")[self._stage_index()])

    def goal_label(self, scene):
        return scene.manager.t(("catch_fruit.goal.warmup", "catch_fruit.goal.steady", "catch_fruit.goal.sprint")[self._stage_index()])

    def reward_summary(self, scene):
        return scene.manager.t("catch_fruit.reward", count=self.best_streak, bonus=self.bonus_hits)

    def next_goal_text(self, scene):
        return scene.manager.t("catch_fruit.next_goal")

    def _stage_index(self):
        session_seconds = self.scene.config.session_seconds
        progress = min(1.0, self.scene.session.session_elapsed / max(1.0, session_seconds)) if session_seconds else 0.0
        if progress < 0.33:
            return 0
        if progress < 0.66:
            return 1
        return 2


class SpotDifferenceMechanic(BaseArcadeMechanic):
    def __init__(self, scene):
        super().__init__(scene)
        self.left_board = None
        self.right_board = None
        self.difference_index = 0
        self.round_hits = 0
        self.total_hits = 0

    def start_round(self):
        super().start_round()
        self.round_hits = 0
        self.difference_index = 0

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.scene.play_area.collidepoint(event.pos):
                self._resolve(True)
        elif event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE:
            self._resolve(True)

    def training_metrics(self, scene):
        return {"round_hits": self.round_hits, "total_hits": self.total_hits}

    def metric_display(self, scene):
        return str(self.total_hits)

    def score_for_outcome(self, success):
        return 10 if success else 0

    def feedback_for_outcome(self, scene, success):
        return ("arcade.play.correct", (86, 174, 112)) if success else ("arcade.play.wrong", (224, 110, 110))

    def stage_label(self, scene):
        return "-"

    def goal_label(self, scene):
        return "-"

    def reward_summary(self, scene):
        return ""

    def next_goal_text(self, scene):
        return ""


class PathFusionMechanic(BaseArcadeMechanic):
    def __init__(self, scene):
        super().__init__(scene)
        self.steps = 0
        self.total_steps = 0

    def start_round(self):
        super().start_round()
        self.steps = 0

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_UP, pygame.K_DOWN, pygame.K_LEFT, pygame.K_RIGHT):
                self.steps += 1
                self.total_steps += 1
                if self.steps >= 5:
                    self._resolve(True)
            elif event.key == pygame.K_SPACE:
                self._resolve(True)

    def training_metrics(self, scene):
        return {"steps": self.steps, "total_steps": self.total_steps}

    def metric_display(self, scene):
        return str(self.total_steps)

    def score_for_outcome(self, success):
        return 10 if success else 0

    def feedback_for_outcome(self, scene, success):
        return ("arcade.play.correct", (86, 174, 112)) if success else ("arcade.play.wrong", (224, 110, 110))

    def stage_label(self, scene):
        return "-"

    def goal_label(self, scene):
        return "-"

    def reward_summary(self, scene):
        return ""

    def next_goal_text(self, scene):
        return ""


class WeakEyeKeyMechanic(BaseArcadeMechanic):
    def __init__(self, scene):
        super().__init__(scene)
        self.key_shape = "round"
        self.key_teeth = 3
        self.total_correct = 0

    def start_round(self):
        super().start_round()
        self.key_shape = random.choice(("round", "square", "triangle"))
        self.key_teeth = random.randint(2, 5)

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_SPACE:
                self._resolve(True)
            elif event.key in (pygame.K_LEFT, pygame.K_RIGHT, pygame.K_UP, pygame.K_DOWN):
                self._resolve(False)

    def training_metrics(self, scene):
        return {"total_correct": self.total_correct}

    def metric_display(self, scene):
        return str(self.total_correct)

    def score_for_outcome(self, success):
        return 10 if success else 0

    def feedback_for_outcome(self, scene, success):
        return ("arcade.play.correct", (86, 174, 112)) if success else ("arcade.play.wrong", (224, 110, 110))

    def stage_label(self, scene):
        return "-"

    def goal_label(self, scene):
        return "-"

    def reward_summary(self, scene):
        return ""

    def next_goal_text(self, scene):
        return ""


class DepthGrabMechanic(BaseArcadeMechanic):
    def __init__(self, scene):
        super().__init__(scene)
        self.grabbed = False
        self.total_grabbed = 0

    def start_round(self):
        super().start_round()
        self.grabbed = False

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE:
            self.grabbed = True
            self.total_grabbed += 1
            self._resolve(True)

    def training_metrics(self, scene):
        return {"total_grabbed": self.total_grabbed}

    def metric_display(self, scene):
        return str(self.total_grabbed)

    def score_for_outcome(self, success):
        return 10 if success else 0

    def feedback_for_outcome(self, scene, success):
        return ("arcade.play.correct", (86, 174, 112)) if success else ("arcade.play.wrong", (224, 110, 110))

    def stage_label(self, scene):
        return "-"

    def goal_label(self, scene):
        return "-"

    def reward_summary(self, scene):
        return ""

    def next_goal_text(self, scene):
        return ""


class PrecisionAimMechanic(BaseArcadeMechanic):
    def __init__(self, scene):
        super().__init__(scene)
        self.target_center = (0, 0)
        self.anchor_center = (0, 0)
        self.aim_center = [0, 0]
        self.base_radius = 44
        self.current_radius = 44
        self.deviations = []
        self.last_quality = "miss"
        self.center_streak = 0
        self.best_center_streak = 0
        self.challenge_shift = 0.0

    def _stage_index(self):
        progress = self.scene.session_progress()
        if progress < 0.34:
            return 0
        if progress < 0.67:
            return 1
        return 2

    def start_round(self):
        super().start_round()
        self.anchor_center = (
            random.randint(self.scene.play_area.left + 80, self.scene.play_area.right - 80),
            random.randint(self.scene.play_area.top + 70, self.scene.play_area.bottom - 70),
        )
        self.target_center = self.anchor_center
        self.aim_center = [self.scene.play_area.centerx, self.scene.play_area.centery]
        stage = self._stage_index()
        difficulty_offset = max(0, int(self.scene.config.difficulty_level) - 3) * 2
        if stage == 0:
            self.base_radius = max(30, 54 - difficulty_offset)
        elif stage == 1:
            self.base_radius = max(22, 42 - difficulty_offset)
        else:
            self.base_radius = max(16, 34 - difficulty_offset)
        self.current_radius = self.base_radius
        self.last_quality = "miss"
        self.challenge_shift = random.uniform(0.0, math.pi * 2)

    def handle_event(self, event):
        if event.type == pygame.MOUSEMOTION:
            self.aim_center[0] = max(self.scene.play_area.left + 20, min(self.scene.play_area.right - 20, event.pos[0]))
            self.aim_center[1] = max(self.scene.play_area.top + 20, min(self.scene.play_area.bottom - 20, event.pos[1]))
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            self._fire_at(self.aim_center[0], self.aim_center[1])
        elif event.type == pygame.KEYDOWN:
            step = 22
            if event.key == pygame.K_LEFT:
                self.aim_center[0] -= step
            elif event.key == pygame.K_RIGHT:
                self.aim_center[0] += step
            elif event.key == pygame.K_UP:
                self.aim_center[1] -= step
            elif event.key == pygame.K_DOWN:
                self.aim_center[1] += step
            elif event.key in (pygame.K_SPACE, pygame.K_RETURN):
                self._fire_at(self.aim_center[0], self.aim_center[1])
            self.aim_center[0] = max(self.scene.play_area.left + 20, min(self.scene.play_area.right - 20, self.aim_center[0]))
            self.aim_center[1] = max(self.scene.play_area.top + 20, min(self.scene.play_area.bottom - 20, self.aim_center[1]))

    def _fire_at(self, x, y):
        if self.outcome is not None:
            return
        dx = x - self.target_center[0]
        dy = y - self.target_center[1]
        distance = math.hypot(dx, dy)
        self.deviations.append(round(distance, 1))
        if distance <= self.current_radius * 0.35:
            self.last_quality = "center"
            self.center_streak += 1
            self.best_center_streak = max(self.best_center_streak, self.center_streak)
            self._resolve(True)
        elif distance <= self.current_radius * 0.68:
            self.last_quality = "good"
            self.center_streak = 0
            self._resolve(True)
        elif distance <= self.current_radius:
            self.last_quality = "edge"
            self.center_streak = 0
            self._resolve(True)
        else:
            self.last_quality = "miss"
            self.center_streak = 0
            self._resolve(False)

    def update(self, now):
        progress = min(1.0, self.scene.round_elapsed / max(1.0, self.scene.config.round_seconds))
        shrink_progress = progress ** 0.78
        self.current_radius = max(10, int(self.base_radius * (1.0 - 0.62 * shrink_progress)))
        if self._stage_index() == 2:
            drift_x = int(math.sin(now * 2.4 + self.challenge_shift) * 18)
            drift_y = int(math.cos(now * 1.9 + self.challenge_shift) * 12)
            self.target_center = (self.anchor_center[0] + drift_x, self.anchor_center[1] + drift_y)
        else:
            self.target_center = self.anchor_center

    def draw(self, screen):
        rings = [self.current_radius, int(self.current_radius * 0.68), int(self.current_radius * 0.35)]
        colors = [(238, 116, 116), (250, 244, 208), (122, 188, 255)]
        for radius, color in zip(rings, colors):
            pygame.draw.circle(screen, color, self.target_center, max(4, radius))
        pygame.draw.circle(screen, (255, 255, 255), self.target_center, rings[-1])
        cross_color = (72, 86, 122)
        cx, cy = int(self.aim_center[0]), int(self.aim_center[1])
        pygame.draw.circle(screen, (255, 255, 255), (cx, cy), 14, 2)
        pygame.draw.line(screen, cross_color, (cx - 12, cy), (cx + 12, cy), 2)
        pygame.draw.line(screen, cross_color, (cx, cy - 12), (cx, cy + 12), 2)
        if self.center_streak >= 2:
            streak = self.scene.small_font.render(
                self.scene.manager.t("arcade.streak", count=self.center_streak),
                True,
                (72, 132, 208),
            )
            screen.blit(streak, (self.scene.play_area.right - streak.get_width() - 12, self.scene.play_area.y + 12))

    def training_metrics(self, scene):
        avg = sum(self.deviations) / len(self.deviations) if self.deviations else 0.0
        return {"average_click_deviation_px": round(avg, 1), "best_center_streak": int(self.best_center_streak)}

    def metric_display(self, scene):
        avg = sum(self.deviations) / len(self.deviations) if self.deviations else 0.0
        return f"{avg:.1f}px"

    def score_for_outcome(self, success):
        if not success:
            return 0
        score = {"center": 18, "good": 12, "edge": 8}.get(self.last_quality, 10)
        if self.last_quality == "center" and self.center_streak >= 2:
            score += 6
        return score

    def feedback_for_outcome(self, scene, success):
        if not success:
            return ("precision_aim.feedback.miss", (214, 96, 96))
        key = {
            "center": "precision_aim.feedback.center",
            "good": "precision_aim.feedback.good",
            "edge": "precision_aim.feedback.edge",
        }.get(self.last_quality, "arcade.play.correct")
        color = {
            "center": (82, 152, 222),
            "good": (86, 174, 112),
            "edge": (214, 148, 88),
        }.get(self.last_quality, (86, 174, 112))
        return (key, color)

    def stage_label(self, scene):
        stage = self._stage_index()
        if stage == 0:
            return scene.manager.t("precision_aim.stage.warmup")
        if stage == 1:
            return scene.manager.t("precision_aim.stage.steady")
        return scene.manager.t("precision_aim.stage.challenge")

    def goal_label(self, scene):
        stage = self._stage_index()
        if stage == 0:
            return scene.manager.t("precision_aim.goal.warmup")
        if stage == 1:
            return scene.manager.t("precision_aim.goal.steady")
        return scene.manager.t("precision_aim.goal.challenge")

    def reward_summary(self, scene):
        return scene.manager.t("precision_aim.reward", count=self.best_center_streak)

    def next_goal_text(self, scene):
        return scene.manager.t("precision_aim.next_goal")