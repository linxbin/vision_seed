import math
import random
import time
from dataclasses import dataclass
from datetime import datetime

import pygame

from core.asset_loader import load_image_if_exists, project_path
from core.base_scene import BaseScene


@dataclass(frozen=True)
class ArcadeGameConfig:
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
    difficulty_level: int = 3
    rounds_total: int = 8
    round_seconds: int = 12
    session_seconds: int = 120
    play_background_style: str | None = None


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
            if event.key == pygame.K_LEFT:
                self.move_dir = -1
            elif event.key == pygame.K_RIGHT:
                self.move_dir = 1
            self._move_basket()
        elif event.type == pygame.KEYUP:
            if event.key == pygame.K_LEFT and self.move_dir < 0:
                self.move_dir = 0
            elif event.key == pygame.K_RIGHT and self.move_dir > 0:
                self.move_dir = 0

    def update(self, now):
        self._move_basket()
        self.fruit_y += self.fruit_speed
        self.space_prompt = self.fruit_y >= self.catch_window_top
        if self.fruit_y >= self.scene.play_area.bottom - 46:
            success = abs(self.fruit_x - self.basket_x) <= 70 and self._clarity() >= 0.55
            self._finalize_catch(success)

    def _move_basket(self):
        if self.move_dir == 0:
            return
        self.basket_x += self.move_dir * self.move_speed
        self.basket_x = max(self.scene.play_area.left + 60, min(self.scene.play_area.right - 60, self.basket_x))

    def _attempt_catch(self):
        if self.outcome is not None:
            return
        success = abs(self.fruit_x - self.basket_x) <= 70 and self._clarity() >= 0.55
        self._finalize_catch(success)

    def _finalize_catch(self, success):
        if self.outcome is not None:
            return
        if success:
            current_size = self._current_size()
            self.smallest_caught = current_size if self.smallest_caught is None else min(self.smallest_caught, current_size)
            if self._clarity() >= 0.75:
                self.clear_hits += 1
            self.streak += 1
            self.best_streak = max(self.best_streak, self.streak)
            self.last_success_bonus = self.fruit_asset_name == "watermelon"
            if self.last_success_bonus:
                self.bonus_hits += 1
        else:
            self.streak = 0
        self._resolve(success)

    def _stage_index(self):
        progress = self.scene.session_progress()
        if progress < 0.34:
            return 0
        if progress < 0.67:
            return 1
        return 2

    def _clarity(self):
        span = max(1, self.scene.play_area.height - 80)
        return min(1.0, max(0.0, (self.fruit_y - self.scene.play_area.top) / span))

    def _current_size(self):
        size = self.start_size - (self.start_size - self.end_size) * self._clarity()
        return int(size)

    def draw(self, screen):
        basket = pygame.Rect(0, 0, 132, 28)
        basket.center = (int(self.basket_x), self.scene.play_area.bottom - 26)
        basket_surface = load_image_if_exists(self.basket_asset, (148, 52))
        if basket_surface is not None:
            screen.blit(basket_surface, basket_surface.get_rect(center=basket.center))
        else:
            pygame.draw.rect(screen, (176, 118, 62), basket, border_radius=14)
            pygame.draw.rect(screen, (238, 213, 184), basket, 2, border_radius=14)

        clarity = self._clarity()
        size = self._current_size()
        halo = pygame.Surface((size * 3, size * 3), pygame.SRCALPHA)
        pygame.draw.circle(halo, (255, 223, 142, int(150 * (1.0 - clarity))), (halo.get_width() // 2, halo.get_height() // 2), size)
        screen.blit(halo, halo.get_rect(center=(int(self.fruit_x), int(self.fruit_y))))
        fruit_surface = load_image_if_exists(self.fruit_assets[self.fruit_asset_name], (size, size))
        if fruit_surface is not None:
            screen.blit(fruit_surface, fruit_surface.get_rect(center=(int(self.fruit_x), int(self.fruit_y))))
        else:
            pygame.draw.circle(screen, (255, 98, 86), (int(self.fruit_x), int(self.fruit_y)), size // 2)
            pygame.draw.circle(screen, (255, 230, 214), (int(self.fruit_x), int(self.fruit_y)), size // 2, 2)
            pygame.draw.line(screen, (124, 168, 92), (self.fruit_x, self.fruit_y - size // 2), (self.fruit_x + 8, self.fruit_y - size // 2 - 16), 3)
    def training_metrics(self, scene):
        return {
            "smallest_caught_size_px": int(self.smallest_caught or self.start_size),
            "clear_window_hits": int(self.clear_hits),
            "best_streak": int(self.best_streak),
            "bonus_hits": int(self.bonus_hits),
        }

    def metric_display(self, scene):
        return f"{self.clear_hits}/{scene.correct_count}"

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


class SpotDifferenceMechanic(BaseArcadeMechanic):
    def __init__(self, scene):
        super().__init__(scene)
        self.left_panel = pygame.Rect(0, 0, 0, 0)
        self.right_panel = pygame.Rect(0, 0, 0, 0)
        self.base_spots = []
        self.diff_index = 0
        self.diff_rect = pygame.Rect(0, 0, 0, 0)

    def start_round(self):
        super().start_round()
        self.left_panel = pygame.Rect(self.scene.play_area.left + 16, self.scene.play_area.top + 18, self.scene.play_area.width // 2 - 28, self.scene.play_area.height - 36)
        self.right_panel = pygame.Rect(self.scene.play_area.centerx + 12, self.scene.play_area.top + 18, self.scene.play_area.width // 2 - 28, self.scene.play_area.height - 36)
        self.base_spots = []
        for _ in range(5):
            self.base_spots.append((random.randint(40, self.left_panel.width - 40), random.randint(40, self.left_panel.height - 40), random.randint(22, 34), random.choice([(246, 174, 112), (122, 190, 255), (162, 228, 168)])))
        self.diff_index = random.randrange(len(self.base_spots))
        x, y, size, _color = self.base_spots[self.diff_index]
        self.diff_rect = pygame.Rect(self.right_panel.x + x - size // 2, self.right_panel.y + y - size // 2, size, size)

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.diff_rect.collidepoint(event.pos):
                self._resolve(True)
            elif self.right_panel.collidepoint(event.pos):
                self._resolve(False)

    def draw(self, screen):
        pygame.draw.rect(screen, (247, 251, 255), self.left_panel, border_radius=12)
        pygame.draw.rect(screen, (247, 251, 255), self.right_panel, border_radius=12)
        pygame.draw.rect(screen, (183, 207, 236), self.left_panel, 2, border_radius=12)
        pygame.draw.rect(screen, (183, 207, 236), self.right_panel, 2, border_radius=12)
        for idx, (x, y, size, color) in enumerate(self.base_spots):
            pygame.draw.circle(screen, color, (self.left_panel.x + x, self.left_panel.y + y), size // 2)
            if idx == self.diff_index:
                pygame.draw.rect(screen, (255, 132, 132), pygame.Rect(self.right_panel.x + x - size // 2, self.right_panel.y + y - size // 2, size, size), border_radius=6)
            else:
                pygame.draw.circle(screen, color, (self.right_panel.x + x, self.right_panel.y + y), size // 2)

    def training_metrics(self, scene):
        return {"binocular_merge_accuracy": round(scene.accuracy_rate(), 1)}

    def metric_display(self, scene):
        return f"{scene.accuracy_rate():.1f}%"


class PathFusionMechanic(BaseArcadeMechanic):
    def __init__(self, scene):
        super().__init__(scene)
        self.left_anchor = (0, 0)
        self.bridge_point = (0, 0)
        self.endpoints = []
        self.correct_index = 0

    def start_round(self):
        super().start_round()
        self.left_anchor = (self.scene.play_area.left + 80, random.randint(self.scene.play_area.top + 70, self.scene.play_area.bottom - 130))
        self.bridge_point = (self.scene.play_area.centerx, random.randint(self.scene.play_area.top + 90, self.scene.play_area.bottom - 110))
        base_y = self.scene.play_area.bottom - 70
        xs = [self.scene.play_area.centerx + 80, self.scene.play_area.centerx + 180, self.scene.play_area.centerx + 280]
        self.endpoints = [(x, base_y) for x in xs]
        self.correct_index = random.randrange(3)

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            for idx, (x, y) in enumerate(self.endpoints):
                if math.hypot(event.pos[0] - x, event.pos[1] - y) <= 26:
                    self._resolve(idx == self.correct_index)
                    break

    def draw(self, screen):
        left_color = (114, 168, 255)
        right_color = (255, 180, 104)
        seam = (self.scene.play_area.centerx, self.bridge_point[1])
        pygame.draw.line(screen, left_color, self.left_anchor, seam, 9)
        pygame.draw.line(screen, right_color, seam, self.endpoints[self.correct_index], 9)
        pygame.draw.line(screen, (215, 226, 240), (self.scene.play_area.centerx, self.scene.play_area.top + 12), (self.scene.play_area.centerx, self.scene.play_area.bottom - 12), 2)
        for idx, point in enumerate(self.endpoints):
            color = right_color if idx == self.correct_index else (206, 217, 232)
            pygame.draw.circle(screen, color, point, 22)
            num = self.scene.small_font.render(str(idx + 1), True, (42, 58, 88))
            screen.blit(num, (point[0] - num.get_width() // 2, point[1] - num.get_height() // 2))

    def training_metrics(self, scene):
        return {"fusion_path_accuracy": round(scene.accuracy_rate(), 1)}

    def metric_display(self, scene):
        return f"{scene.accuracy_rate():.1f}%"

class WeakEyeKeyMechanic(BaseArcadeMechanic):
    def __init__(self, scene):
        super().__init__(scene)
        self.board = pygame.Rect(0, 0, 0, 0)
        self.clue_panel = pygame.Rect(0, 0, 0, 0)
        self.key_rect = pygame.Rect(0, 0, 0, 0)
        self.decoys = []

    def start_round(self):
        super().start_round()
        self.board = pygame.Rect(self.scene.play_area.left + 18, self.scene.play_area.top + 18, self.scene.play_area.width - 220, self.scene.play_area.height - 36)
        self.clue_panel = pygame.Rect(self.board.right + 18, self.board.y, 164, self.board.height)
        self.decoys = []
        for _ in range(10):
            self.decoys.append((random.randint(self.board.left + 24, self.board.right - 24), random.randint(self.board.top + 24, self.board.bottom - 24), random.choice([(240, 206, 120), (126, 188, 255), (188, 210, 236)])))
        key_x = random.randint(self.board.left + 40, self.board.right - 70)
        key_y = random.randint(self.board.top + 40, self.board.bottom - 30)
        self.key_rect = pygame.Rect(key_x, key_y, 44, 20)

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.key_rect.collidepoint(event.pos):
                self._resolve(True)
            elif self.board.collidepoint(event.pos):
                self._resolve(False)

    def draw(self, screen):
        pygame.draw.rect(screen, (248, 251, 255), self.board, border_radius=14)
        pygame.draw.rect(screen, (244, 248, 252), self.clue_panel, border_radius=14)
        pygame.draw.rect(screen, (184, 206, 228), self.board, 2, border_radius=14)
        pygame.draw.rect(screen, (184, 206, 228), self.clue_panel, 2, border_radius=14)
        for x, y, color in self.decoys:
            pygame.draw.circle(screen, color, (x, y), 12)
        self._draw_key(screen, self.key_rect.x, self.key_rect.y, 1.0, (244, 196, 102))
        hint = self.scene.small_font.render(self.scene.manager.t('weak_eye_key.clue'), True, (70, 90, 120))
        screen.blit(hint, (self.clue_panel.x + 14, self.clue_panel.y + 20))
        self._draw_key(screen, self.clue_panel.x + 40, self.clue_panel.y + 78, 1.8, (244, 196, 102))

    def _draw_key(self, screen, x, y, scale, color):
        head_r = int(9 * scale)
        pygame.draw.circle(screen, color, (int(x + head_r), int(y + head_r)), head_r, 3)
        pygame.draw.rect(screen, color, pygame.Rect(int(x + head_r * 2), int(y + head_r - 3 * scale), int(24 * scale), int(6 * scale)), border_radius=3)
        pygame.draw.rect(screen, color, pygame.Rect(int(x + head_r * 2 + 12 * scale), int(y + head_r - 3 * scale), int(4 * scale), int(14 * scale)), border_radius=2)
        pygame.draw.rect(screen, color, pygame.Rect(int(x + head_r * 2 + 20 * scale), int(y + head_r - 3 * scale), int(4 * scale), int(10 * scale)), border_radius=2)

    def training_metrics(self, scene):
        return {"weak_eye_usage_rate": round(scene.accuracy_rate(), 1)}

    def metric_display(self, scene):
        return f"{scene.accuracy_rate():.1f}%"


class DepthGrabMechanic(BaseArcadeMechanic):
    def __init__(self, scene):
        super().__init__(scene)
        self.targets = []
        self.correct_index = 0

    def start_round(self):
        super().start_round()
        ys = [self.scene.play_area.centery - 40, self.scene.play_area.centery + 20, self.scene.play_area.centery - 10]
        xs = [self.scene.play_area.left + 150, self.scene.play_area.centerx, self.scene.play_area.right - 150]
        order = [0, 1, 2]
        random.shuffle(order)
        self.correct_index = order[0]
        self.targets = []
        for idx, x in enumerate(xs):
            depth_rank = order[idx]
            scale = 1.3 - depth_rank * 0.22
            self.targets.append({"center": (x, ys[idx]), "radius": int(34 * scale), "depth_rank": depth_rank})

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            for idx, target in enumerate(self.targets):
                x, y = target["center"]
                if math.hypot(event.pos[0] - x, event.pos[1] - y) <= target["radius"]:
                    self._resolve(idx == self.correct_index)
                    break

    def draw(self, screen):
        for idx, target in enumerate(self.targets):
            x, y = target["center"]
            radius = target["radius"]
            shadow_offset = 12 - target["depth_rank"] * 4
            pygame.draw.circle(screen, (208, 220, 234), (x + shadow_offset, y + shadow_offset), radius)
            color = (255, 212, 122) if idx == self.correct_index else (138, 192, 255)
            pygame.draw.circle(screen, color, (x, y), radius)
            pygame.draw.circle(screen, (255, 255, 255), (x, y), radius, 2)

    def training_metrics(self, scene):
        return {"depth_accuracy": round(scene.accuracy_rate(), 1)}

    def metric_display(self, scene):
        return f"{scene.accuracy_rate():.1f}%"


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
            streak = self.scene.small_font.render(f"STREAK x{self.center_streak}", True, (72, 132, 208))
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


MECHANICS = {
    "catch_fruit": CatchFruitMechanic,
    "spot_difference": SpotDifferenceMechanic,
    "path_fusion": PathFusionMechanic,
    "weak_eye_key": WeakEyeKeyMechanic,
    "depth_grab": DepthGrabMechanic,
    "precision_aim": PrecisionAimMechanic,
}


class ArcadeTrainingScene(BaseScene):
    STATE_HOME = "home"
    STATE_HELP = "help"
    STATE_PLAY = "play"
    STATE_RESULT = "result"

    def __init__(self, manager, config):
        super().__init__(manager)
        self.config = config
        self.width = 900
        self.height = 700
        self.state = self.STATE_HOME
        self.attempt_count = 0
        self.correct_count = 0
        self.wrong_count = 0
        self.score = 0
        self.session_started_at = 0.0
        self.round_started_at = 0.0
        self.session_elapsed = 0.0
        self.round_elapsed = 0.0
        self.feedback_text = ""
        self.feedback_until = 0.0
        self.final_stats = {}
        self._result_saved = False
        self.home_focus = 0
        self.result_focus = 0
        self.completed_sound_played = False
        self._refresh_fonts()
        self._build_ui_rects()
        self.mechanic = MECHANICS[config.mechanic_type](self)
        self.completed_sound_played = False

    def _session_seconds(self):
        try:
            minutes = int(self.manager.settings.get("session_duration_minutes", 5))
        except (TypeError, ValueError):
            minutes = 5
        return max(60, minutes * 60)

    def session_progress(self):
        return min(1.0, self.session_elapsed / max(1.0, self._session_seconds()))

    def _refresh_fonts(self):
        self.title_font = self.create_font(52)
        self.subtitle_font = self.create_font(26)
        self.option_font = self.create_font(28)
        self.body_font = self.create_font(22)
        self.small_font = self.create_font(18)

    def _build_ui_rects(self):
        self.play_area = pygame.Rect(54, 104, self.width - 108, self.height - 176)
        card_w = min(560, self.width - 120)
        card_h = 62
        start_x = self.width // 2 - card_w // 2
        start_y = 220
        self.btn_start = pygame.Rect(start_x, start_y, card_w, card_h)
        self.btn_help = pygame.Rect(start_x, start_y + 82, card_w, card_h)
        self.btn_back = pygame.Rect(self.width - 108, 18, 88, 36)
        self.btn_ok = pygame.Rect(self.width // 2 - 90, self.height - 92, 180, 54)
        self.btn_home = pygame.Rect(self.width - 108, 18, 88, 36)
        self.btn_continue = pygame.Rect(self.width // 2 - 210, self.height - 100, 180, 48)
        self.btn_exit = pygame.Rect(self.width // 2 + 30, self.height - 100, 180, 48)

    def on_resize(self, width, height):
        self.width = width
        self.height = height
        self._build_ui_rects()

    def reset(self):
        self.state = self.STATE_HOME
        self.attempt_count = 0
        self.correct_count = 0
        self.wrong_count = 0
        self.score = 0
        self.session_started_at = 0.0
        self.round_started_at = 0.0
        self.session_elapsed = 0.0
        self.round_elapsed = 0.0
        self.feedback_text = ""
        self.feedback_until = 0.0
        self.final_stats = {}
        self._result_saved = False

    def accuracy_rate(self):
        total = self.correct_count + self.wrong_count
        return round((self.correct_count / total) * 100, 1) if total else 0.0

    def _set_feedback(self, key, color):
        self.feedback_text = self.manager.t(key)
        self.feedback_color = color
        self.feedback_until = time.time() + 1.0

    def _play_feedback_sound(self, success):
        sound_manager = getattr(self.manager, 'sound_manager', None)
        if not sound_manager:
            return
        if success:
            sound_manager.play_correct()
        else:
            sound_manager.play_wrong()

    def _start_session(self):
        self.state = self.STATE_PLAY
        self.attempt_count = 0
        self.correct_count = 0
        self.wrong_count = 0
        self.score = 0
        self.session_started_at = time.time()
        self._result_saved = False
        self._start_round()

    def _start_round(self):
        self.round_started_at = time.time()
        self.round_elapsed = 0.0
        self.mechanic.start_round()

    def _apply_outcome(self, success):
        self._play_feedback_sound(success)
        points = self.mechanic.score_for_outcome(success)
        key, color = self.mechanic.feedback_for_outcome(self, success)
        if success:
            self.correct_count += 1
            self.score += points
            self._set_feedback(key, color)
            if points > 10:
                self.feedback_text = f"{self.feedback_text}  +{points}"
        else:
            self.wrong_count += 1
            self._set_feedback(key, color)
        self.attempt_count += 1
        if self.session_elapsed >= self._session_seconds():
            self._finish_session()
        else:
            self._start_round()

    def _finish_session(self):
        self.state = self.STATE_RESULT
        duration = max(0.0, self.session_elapsed)
        self.final_stats = {
            "duration": int(duration),
            "correct": self.correct_count,
            "wrong": self.wrong_count,
            "accuracy": self.accuracy_rate(),
            "difficulty_level": self.config.difficulty_level,
            "score": self.score,
            "metric_label": self.manager.t(self.config.metric_label_key),
            "metric_value": self.mechanic.metric_display(self),
            "reward_summary": self.mechanic.reward_summary(self),
            "next_goal": self.mechanic.next_goal_text(self),
            "stars": max(1, min(3, int(round(self.accuracy_rate() / 33.4)))),
        }
        if not self._result_saved:
            payload = {
                "timestamp": datetime.now().replace(microsecond=0).isoformat(),
                "game_id": self.config.game_id,
                "difficulty_level": self.config.difficulty_level,
                "total_questions": self.correct_count + self.wrong_count,
                "correct_count": self.correct_count,
                "wrong_count": self.wrong_count,
                "duration_seconds": round(duration, 1),
                "training_metrics": self.mechanic.training_metrics(self),
            }
            self.manager.current_result = {"correct": self.correct_count, "total": self.correct_count + self.wrong_count, "game_id": self.config.game_id}
            self.manager.data_manager.save_training_session(payload)
            self.saved_session = payload
            self._result_saved = True
        sound_manager = getattr(self.manager, 'sound_manager', None)
        if sound_manager and not self.completed_sound_played:
            sound_manager.play_completed()
            self.completed_sound_played = True

    def _go_category(self):
        self.manager.set_scene("category")

    def _go_menu(self):
        self.manager.set_scene("menu")

    def _home_buttons(self):
        return [self.btn_start, self.btn_help, self.btn_back]

    def _result_buttons(self):
        return [self.btn_continue, self.btn_exit]

    def handle_events(self, events):
        for event in events:
            if self.state == self.STATE_HOME:
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        self._go_category()
                    elif event.key in (pygame.K_UP, pygame.K_LEFT):
                        self.home_focus = (self.home_focus - 1) % 3
                    elif event.key in (pygame.K_DOWN, pygame.K_RIGHT):
                        self.home_focus = (self.home_focus + 1) % 3
                    elif event.key == pygame.K_1:
                        self._start_session()
                    elif event.key == pygame.K_2:
                        self.state = self.STATE_HELP
                    elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
                        if self.home_focus == 0:
                            self._start_session()
                        elif self.home_focus == 1:
                            self.state = self.STATE_HELP
                        else:
                            self._go_category()
                elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    pos = getattr(event, "pos", pygame.mouse.get_pos())
                    if self.btn_back.collidepoint(pos):
                        self.home_focus = 2
                        self._go_category()
                    elif self.btn_start.collidepoint(pos):
                        self.home_focus = 0
                        self._start_session()
                    elif self.btn_help.collidepoint(pos):
                        self.home_focus = 1
                        self.state = self.STATE_HELP
            elif self.state == self.STATE_HELP:
                if event.type == pygame.KEYDOWN and event.key in (pygame.K_ESCAPE, pygame.K_RETURN):
                    self.state = self.STATE_HOME
                elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1 and self.btn_ok.collidepoint(getattr(event, 'pos', pygame.mouse.get_pos())):
                    self.state = self.STATE_HOME
            elif self.state == self.STATE_PLAY:
                if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                    self._go_category()
                    continue
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1 and self.btn_home.collidepoint(getattr(event, 'pos', pygame.mouse.get_pos())):
                    self._go_category()
                    continue
                self.mechanic.handle_event(event)
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
                        self.result_focus = 0
                        self.state = self.STATE_HOME
                    elif self.btn_exit.collidepoint(pos):
                        self.result_focus = 1
                        self._go_menu()

    def update(self):
        now = time.time()
        if self.state == self.STATE_PLAY:
            self.session_elapsed = now - self.session_started_at
            self.round_elapsed = now - self.round_started_at
            if self.session_elapsed >= self._session_seconds():
                self._finish_session()
                return
            self.mechanic.update(now)
            if self.round_elapsed >= self.config.round_seconds and self.mechanic.outcome is None:
                self.mechanic._resolve(False)
            outcome = self.mechanic.consume_outcome()
            if outcome is not None:
                self._apply_outcome(outcome)
        if self.feedback_text and now > self.feedback_until:
            self.feedback_text = ""

    def _draw_gradient_bg(self, screen):
        top = tuple(min(255, c + 88) for c in self.config.theme_color)
        bottom = (226, 237, 248)
        for y in range(self.height):
            t = y / max(1, self.height - 1)
            color = (
                int(top[0] * (1 - t) + bottom[0] * t),
                int(top[1] * (1 - t) + bottom[1] * t),
                int(top[2] * (1 - t) + bottom[2] * t),
            )
            pygame.draw.line(screen, color, (0, y), (self.width, y))

        self._draw_theme_decorations(screen)

    def _draw_amblyopia_stimulus_bg(self, screen):
        pattern_rect = self.play_area.inflate(-12, -12)
        elapsed = time.time() - self.session_started_at if self.session_started_at else time.time()
        pattern_index = int(elapsed // 3) % 2
        motion = int((elapsed * 36) % 48)
        pattern_surface = pygame.Surface(pattern_rect.size, pygame.SRCALPHA)
        if pattern_index == 0:
            block = 32
            for x in range(-block, pattern_rect.width + block, block):
                for y in range(-block, pattern_rect.height + block, block):
                    shifted_x = x + (motion if (y // block) % 2 == 0 else -motion)
                    color = (245, 245, 245) if ((x // block) + (y // block)) % 2 == 0 else (18, 18, 18)
                    pygame.draw.rect(pattern_surface, color, pygame.Rect(shifted_x, y, block, block))
        else:
            stripe = 28
            for idx, x in enumerate(range(-stripe * 2, pattern_rect.width + stripe * 2, stripe)):
                shifted = x + motion
                color = (248, 248, 248) if idx % 2 == 0 else (12, 12, 12)
                pygame.draw.rect(pattern_surface, color, pygame.Rect(shifted, 0, stripe, pattern_rect.height))
        mask_surface = pygame.Surface(pattern_rect.size, pygame.SRCALPHA)
        pygame.draw.rect(mask_surface, (255, 255, 255, 255), mask_surface.get_rect(), border_radius=18)
        pattern_surface.blit(mask_surface, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
        screen.blit(pattern_surface, pattern_rect.topleft)
        pygame.draw.rect(screen, (255, 255, 255), pattern_rect, 2, border_radius=18)

    def _draw_theme_decorations(self, screen):
        color = self.config.theme_color
        now = time.time()
        if self.config.mechanic_type == 'catch_fruit':
            for idx in range(4):
                x = int(100 + idx * 180 + math.sin(now * 0.8 + idx) * 18)
                y = 70 + idx * 10
                pygame.draw.circle(screen, (255, 214, 184), (x, y), 18)
                pygame.draw.circle(screen, color, (x, y + 6), 14)
        elif self.config.mechanic_type == 'spot_difference':
            for idx in range(5):
                x = 90 + idx * 150
                y = 78 + int(math.sin(now * 1.2 + idx) * 6)
                if idx % 2 == 0:
                    pygame.draw.circle(screen, color, (x, y), 12)
                else:
                    pygame.draw.rect(screen, color, pygame.Rect(x - 12, y - 12, 24, 24), border_radius=6)
        elif self.config.mechanic_type == 'path_fusion':
            pygame.draw.line(screen, (255, 190, 122), (70, 84), (self.width // 2, 54), 6)
            pygame.draw.line(screen, color, (self.width // 2, 54), (self.width - 80, 92), 6)
        elif self.config.mechanic_type == 'weak_eye_key':
            for idx in range(3):
                self._draw_key_deco(screen, 90 + idx * 150, 70 + idx * 8, 0.9 + idx * 0.1)
        elif self.config.mechanic_type == 'depth_grab':
            for idx, radius in enumerate((22, 16, 12)):
                x = 110 + idx * 160
                y = 78 + idx * 6
                pygame.draw.circle(screen, (210, 220, 234), (x + 10, y + 10), radius)
                pygame.draw.circle(screen, color, (x, y), radius)
        elif self.config.mechanic_type == 'precision_aim':
            center = (110, 78)
            for radius, ring_color in ((28, color), (18, (250, 244, 208)), (8, (255, 255, 255))):
                pygame.draw.circle(screen, ring_color, center, radius, 3 if radius > 10 else 0)

    def _draw_key_deco(self, screen, x, y, scale):
        color = (244, 196, 102)
        head_r = int(9 * scale)
        pygame.draw.circle(screen, color, (int(x + head_r), int(y + head_r)), head_r, 3)
        pygame.draw.rect(screen, color, pygame.Rect(int(x + head_r * 2), int(y + head_r - 3 * scale), int(24 * scale), int(6 * scale)), border_radius=3)
        pygame.draw.rect(screen, color, pygame.Rect(int(x + head_r * 2 + 12 * scale), int(y + head_r - 3 * scale), int(4 * scale), int(14 * scale)), border_radius=2)

    def _load_ui_icon(self, icon_name, light=False, size=(18, 18)):
        suffix = "light" if light else "dark"
        return load_image_if_exists(project_path("assets", "ui", f"{icon_name}_{suffix}.png"), size)

    def _draw_help_illustration(self, screen):
        card = pygame.Rect(self.width // 2 - 180, 154, 360, 118)
        pygame.draw.rect(screen, (248, 252, 255), card, border_radius=18)
        pygame.draw.rect(screen, (190, 209, 232), card, 2, border_radius=18)
        cx = card.centerx
        cy = card.centery + 6
        kind = self.config.mechanic_type
        if kind == "catch_fruit":
            pygame.draw.rect(screen, (180, 122, 72), pygame.Rect(cx - 64, cy + 26, 128, 20), border_radius=10)
            for idx, radius in enumerate((20, 16, 12)):
                fy = cy - 28 + idx * 24
                pygame.draw.circle(screen, (255, 110, 96), (cx - 70 + idx * 70, fy), radius)
                pygame.draw.circle(screen, (255, 233, 218), (cx - 70 + idx * 70, fy), radius, 2)
        elif kind == "spot_difference":
            left = pygame.Rect(cx - 140, cy - 42, 110, 84)
            right = pygame.Rect(cx + 30, cy - 42, 110, 84)
            pygame.draw.rect(screen, (241, 247, 255), left, border_radius=12)
            pygame.draw.rect(screen, (241, 247, 255), right, border_radius=12)
            pygame.draw.rect(screen, (170, 194, 226), left, 2, border_radius=12)
            pygame.draw.rect(screen, (170, 194, 226), right, 2, border_radius=12)
            for ox in (24, 56, 84):
                pygame.draw.circle(screen, self.config.theme_color, (left.x + ox, left.y + 28), 8)
                pygame.draw.circle(screen, self.config.theme_color, (right.x + ox, right.y + 28), 8)
            pygame.draw.circle(screen, self.config.theme_color, (left.x + 54, left.y + 58), 8)
            pygame.draw.rect(screen, (255, 126, 126), pygame.Rect(right.x + 46, right.y + 50, 18, 18), border_radius=4)
        elif kind == "path_fusion":
            pygame.draw.line(screen, (120, 174, 255), (cx - 140, cy - 28), (cx - 18, cy - 2), 10)
            pygame.draw.line(screen, (255, 192, 118), (cx + 18, cy - 2), (cx + 140, cy + 26), 10)
            pygame.draw.line(screen, (218, 228, 240), (cx, cy - 52), (cx, cy + 54), 2)
            for idx, px in enumerate((cx + 70, cx + 112, cx + 152)):
                pygame.draw.circle(screen, (220, 228, 240) if idx != 1 else (255, 192, 118), (px, cy + 30), 14)
        elif kind == "weak_eye_key":
            board = pygame.Rect(cx - 150, cy - 42, 210, 92)
            clue = pygame.Rect(cx + 78, cy - 42, 58, 92)
            pygame.draw.rect(screen, (242, 248, 255), board, border_radius=12)
            pygame.draw.rect(screen, (247, 250, 254), clue, border_radius=12)
            pygame.draw.rect(screen, (180, 204, 228), board, 2, border_radius=12)
            pygame.draw.rect(screen, (180, 204, 228), clue, 2, border_radius=12)
            for ix in range(4):
                pygame.draw.circle(screen, (188, 210, 236), (board.x + 34 + ix * 40, board.y + 30), 9)
            self._draw_key_deco(screen, board.x + 86, board.y + 46, 0.8)
            self._draw_key_deco(screen, clue.x + 6, clue.y + 30, 1.0)
        elif kind == "depth_grab":
            for idx, radius in enumerate((24, 18, 13)):
                x = cx - 90 + idx * 90
                y = cy - 8 + idx * 8
                pygame.draw.circle(screen, (206, 220, 235), (x + 12, y + 12), radius)
                pygame.draw.circle(screen, self.config.theme_color if idx == 0 else (138, 192, 255), (x, y), radius)
        elif kind == "precision_aim":
            target = (cx, cy)
            for radius, color in ((34, self.config.theme_color), (22, (248, 242, 206)), (10, (255, 255, 255))):
                pygame.draw.circle(screen, color, target, radius, 3 if radius > 12 else 0)
            pygame.draw.line(screen, (96, 116, 150), (cx + 58, cy - 58), (cx + 18, cy - 18), 4)
            pygame.draw.line(screen, (96, 116, 150), (cx + 58, cy - 58), (cx + 58, cy - 24), 4)

    def _badge_text(self):
        badges = {
            'catch_fruit': 'FOCUS',
            'spot_difference': 'SYNC',
            'path_fusion': 'FUSE',
            'weak_eye_key': 'CLUE',
            'depth_grab': 'DEPTH',
            'precision_aim': 'AIM',
        }
        return badges.get(self.config.mechanic_type, 'PLAY')

    def _draw_button(self, screen, rect, text, color, text_color=(255, 255, 255), icon_name=None, selected=False):
        hovered = rect.collidepoint(pygame.mouse.get_pos())
        fill = tuple(min(255, c + 16) for c in color) if hovered or selected else color
        border_color = (255, 250, 212) if selected else (255, 255, 255)
        if selected:
            glow = rect.inflate(10, 10)
            pygame.draw.rect(screen, (255, 236, 176), glow, border_radius=16)
        pygame.draw.rect(screen, fill, rect, border_radius=12)
        pygame.draw.rect(screen, border_color, rect, 3 if selected else 2, border_radius=12)
        label = self.option_font.render(text, True, text_color)
        icon = self._load_ui_icon(icon_name, light=sum(text_color) > 500, size=(18, 18)) if icon_name else None
        gap = 8 if icon is not None else 0
        content_width = label.get_width() + (icon.get_width() + gap if icon is not None else 0)
        start_x = rect.centerx - content_width // 2
        if icon is not None:
            screen.blit(icon, (start_x, rect.centery - icon.get_height() // 2))
            start_x += icon.get_width() + gap
        screen.blit(label, (start_x, rect.centery - label.get_height() // 2))

    def _draw_home(self, screen):
        badge_rect = pygame.Rect(self.width // 2 - 62, 52, 124, 28)
        pygame.draw.rect(screen, self.config.theme_color, badge_rect, border_radius=14)
        badge = self.small_font.render(self._badge_text(), True, (255, 255, 255))
        screen.blit(badge, (badge_rect.centerx - badge.get_width() // 2, badge_rect.centery - badge.get_height() // 2))
        title = self.title_font.render(self.manager.t(self.config.title_key), True, (34, 60, 96))
        subtitle = self.subtitle_font.render(self.manager.t(self.config.subtitle_key), True, (86, 104, 130))
        screen.blit(title, (self.width // 2 - title.get_width() // 2, 86))
        screen.blit(subtitle, (self.width // 2 - subtitle.get_width() // 2, 142))
        self._draw_button(screen, self.btn_start, self.manager.t("arcade.home.start"), self.config.theme_color, icon_name="check", selected=self.home_focus == 0)
        self._draw_button(screen, self.btn_help, self.manager.t("arcade.home.help"), (120, 138, 170), icon_name="question", selected=self.home_focus == 1)
        self._draw_button(screen, self.btn_back, self.manager.t("common.back"), (86, 116, 170), icon_name="back_arrow", selected=self.home_focus == 2)
        hint = self.small_font.render(self.manager.t("arcade.home.tip"), True, (86, 104, 130))
        screen.blit(hint, (self.width // 2 - hint.get_width() // 2, self.btn_help.bottom + 22))

    def _draw_help(self, screen):
        title = self.title_font.render(self.manager.t("arcade.help.title"), True, (38, 64, 100))
        screen.blit(title, (self.width // 2 - title.get_width() // 2, 86))
        self._draw_help_illustration(screen)
        for idx, key in enumerate(self.config.help_steps, start=1):
            icon_x = 118
            y = 314 + (idx - 1) * 82
            pygame.draw.circle(screen, self.config.theme_color, (icon_x, y + 12), 16)
            num = self.small_font.render(str(idx), True, (255, 255, 255))
            screen.blit(num, (icon_x - num.get_width() // 2, y + 12 - num.get_height() // 2))
            text = self.body_font.render(self.manager.t(key), True, (58, 84, 118))
            screen.blit(text, (156, y))
        self._draw_button(screen, self.btn_ok, self.manager.t("arcade.help.ok"), (244, 214, 126), text_color=(110, 88, 46), icon_name="check")

    def _draw_play(self, screen):
        if self.config.play_background_style == "amblyopia_stimulus":
            pygame.draw.rect(screen, (236, 236, 236), self.play_area, border_radius=18)
            self._draw_amblyopia_stimulus_bg(screen)
        else:
            pygame.draw.rect(screen, (245, 250, 255), self.play_area, border_radius=16)
            pygame.draw.rect(screen, (182, 204, 226), self.play_area, 2, border_radius=16)
        timer = max(0, int(self._session_seconds() - self.session_elapsed))
        items = [
            self.manager.t("arcade.time_left", sec=f"{timer // 60:02d}:{timer % 60:02d}"),
            self.manager.t("arcade.score", score=self.score),
        ]
        for idx, text in enumerate(items):
            surf = self.small_font.render(text, True, (56, 82, 118))
            screen.blit(surf, (24 + idx * 240, 20))
        stage = self.small_font.render(self.manager.t("arcade.play.stage", stage=self.mechanic.stage_label(self)), True, (72, 92, 126))
        goal = self.small_font.render(self.manager.t("arcade.play.goal", goal=self.mechanic.goal_label(self)), True, (82, 100, 126))
        screen.blit(stage, (24, 52))
        screen.blit(goal, (24, 76))
        self._draw_button(screen, self.btn_home, self.manager.t("common.back"), (86, 116, 170), icon_name="back_arrow")
        guide = self.small_font.render(self.manager.t(self.config.guide_key), True, (82, 100, 126))
        screen.blit(guide, (self.play_area.centerx - guide.get_width() // 2, self.play_area.bottom + 10))
        self.mechanic.draw(screen)
        if self.feedback_text:
            fb = self.body_font.render(self.feedback_text, True, self.feedback_color)
            screen.blit(fb, (self.width // 2 - fb.get_width() // 2, self.play_area.y - 38))

    def _draw_result(self, screen):
        badge_rect = pygame.Rect(self.width // 2 - 70, 62, 140, 30)
        pygame.draw.rect(screen, self.config.theme_color, badge_rect, border_radius=15)
        badge = self.small_font.render(self._badge_text(), True, (255, 255, 255))
        screen.blit(badge, (badge_rect.centerx - badge.get_width() // 2, badge_rect.centery - badge.get_height() // 2))
        title = self.title_font.render(self.manager.t("arcade.result.title"), True, (42, 70, 108))
        screen.blit(title, (self.width // 2 - title.get_width() // 2, 100))
        lines = [
            self.manager.t("arcade.result.duration", sec=self.final_stats.get("duration", 0)),
            self.manager.t("arcade.result.correct", n=self.final_stats.get("correct", 0)),
            self.manager.t("arcade.result.wrong", n=self.final_stats.get("wrong", 0)),
            self.manager.t("arcade.result.accuracy", value=self.final_stats.get("accuracy", 0.0)),
            self.manager.t("arcade.result.difficulty", level=self.final_stats.get("difficulty_level", self.config.difficulty_level)),
            self.manager.t("arcade.result.metric", label=self.final_stats.get("metric_label", "-"), value=self.final_stats.get("metric_value", "-")),
            self.manager.t("arcade.result.stars", count=self.final_stats.get("stars", 1)),
            self.manager.t("arcade.result.reward", reward=self.final_stats.get("reward_summary", "-")),
            self.manager.t("arcade.result.next_goal", goal=self.final_stats.get("next_goal", "-")),
        ]
        for idx, text in enumerate(lines):
            surf = self.body_font.render(text, True, (58, 84, 118))
            screen.blit(surf, (self.width // 2 - surf.get_width() // 2, 176 + idx * 34))
        self._draw_button(screen, self.btn_continue, self.manager.t("arcade.result.continue"), (86, 152, 114), icon_name="check", selected=self.result_focus == 0)
        self._draw_button(screen, self.btn_exit, self.manager.t("arcade.result.exit"), (120, 134, 168), icon_name="cross", selected=self.result_focus == 1)

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
