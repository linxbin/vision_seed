import math
import random

import pygame
import pygame.surfarray

from core.asset_loader import load_image_if_exists, project_path


class EyeFindPatternService:
    PATTERN_IDS = ("star", "cat", "butterfly", "moon", "fish", "rocket")
    PATTERN_COLORS = (
        (255, 214, 140, 255),
        (154, 227, 168, 255),
        (160, 205, 255, 255),
        (252, 174, 174, 255),
    )
    GLASSES_BACKGROUND = (255, 19, 255, 179)
    RED_FILTER = (255, 0, 0, 255)
    BLUE_FILTER = (0, 0, 255, 255)

    def _asset_path(self, pattern_id):
        return project_path("games", "simultaneous", "eye_find_patterns", "assets", "objects", f"{pattern_id}.png")

    def build_pattern_surface(self, pattern_id, size, color):
        asset_surface = load_image_if_exists(self._asset_path(pattern_id), (size, size))
        if asset_surface is not None:
            return asset_surface

        surf = pygame.Surface((size, size), pygame.SRCALPHA)
        cx = size // 2
        cy = size // 2
        if pattern_id == "star":
            points = []
            for i in range(10):
                angle = -math.pi / 2 + i * math.pi / 5
                radius = size * (0.38 if i % 2 == 0 else 0.18)
                points.append((cx + int(math.cos(angle) * radius), cy + int(math.sin(angle) * radius)))
            pygame.draw.polygon(surf, color, points)
        elif pattern_id == "cat":
            pygame.draw.circle(surf, color, (cx, cy + 8), int(size * 0.26))
            pygame.draw.polygon(surf, color, [(cx - 44, cy - 18), (cx - 18, cy - 48), (cx - 8, cy - 14)])
            pygame.draw.polygon(surf, color, [(cx + 44, cy - 18), (cx + 18, cy - 48), (cx + 8, cy - 14)])
            pygame.draw.circle(surf, (50, 58, 72, 255), (cx - 16, cy + 8), 4)
            pygame.draw.circle(surf, (50, 58, 72, 255), (cx + 16, cy + 8), 4)
        elif pattern_id == "butterfly":
            pygame.draw.ellipse(surf, color, pygame.Rect(cx - 56, cy - 34, 46, 54))
            pygame.draw.ellipse(surf, color, pygame.Rect(cx + 10, cy - 34, 46, 54))
            pygame.draw.ellipse(surf, color, pygame.Rect(cx - 50, cy + 6, 40, 48))
            pygame.draw.ellipse(surf, color, pygame.Rect(cx + 10, cy + 6, 40, 48))
            pygame.draw.rect(surf, (72, 82, 102, 255), pygame.Rect(cx - 5, cy - 24, 10, 68), border_radius=6)
        else:
            pygame.draw.circle(surf, color, (cx, cy), int(size * 0.28))
            pygame.draw.circle(surf, (255, 255, 255, 120), (cx - 12, cy - 10), int(size * 0.09))
        return surf

    def next_pattern(self, size=140):
        pattern_id = random.choice(self.PATTERN_IDS)
        color = random.choice(self.PATTERN_COLORS)
        return {
            "pattern_id": pattern_id,
            "color": color,
            "surface": self.build_pattern_surface(pattern_id, size, color),
        }

    def reset_positions(self, width, height):
        left_center = (width // 2 - 140, height // 2 + 10)
        right_center = (
            left_center[0] + random.choice([90, 120, 150, 180]),
            left_center[1] + random.choice([-20, -10, 0, 10, 20]),
        )
        return left_center, right_center

    def apply_filter(self, base, mode, filter_direction, side, mode_glasses, filter_lr):
        if mode != mode_glasses:
            return base
        is_left_red = filter_direction == filter_lr
        use_red = (side == "left" and is_left_red) or (side == "right" and not is_left_red)
        color = self.RED_FILTER if use_red else self.BLUE_FILTER
        result = pygame.Surface(base.get_size(), pygame.SRCALPHA)
        result.fill(color)
        base_alpha = pygame.surfarray.array_alpha(base)
        result_alpha = pygame.surfarray.pixels_alpha(result)
        tint_alpha = color[3]
        result_alpha[:] = (base_alpha.astype("uint16") * tint_alpha // 255).astype("uint8")
        del result_alpha
        return result

    def blend_filtered_patterns(self, canvas_size, left_surface, left_rect, right_surface, right_rect):
        left_layer = pygame.Surface(canvas_size, pygame.SRCALPHA)
        right_layer = pygame.Surface(canvas_size, pygame.SRCALPHA)
        left_layer.blit(left_surface, left_rect)
        right_layer.blit(right_surface, right_rect)

        left_rgb = pygame.surfarray.array3d(left_layer).astype("uint16")
        right_rgb = pygame.surfarray.array3d(right_layer).astype("uint16")
        left_alpha = pygame.surfarray.array_alpha(left_layer).astype("uint16")
        right_alpha = pygame.surfarray.array_alpha(right_layer).astype("uint16")

        output_rgb = left_rgb.copy()
        output_alpha = left_alpha.copy()

        only_right = (left_alpha == 0) & (right_alpha > 0)
        output_rgb[only_right] = right_rgb[only_right]
        output_alpha[only_right] = right_alpha[only_right]

        overlap = (left_alpha > 0) & (right_alpha > 0)
        if overlap.any():
            # Use multiplicative filter mixing in overlap regions so red/blue
            # layers combine like stacked color filters instead of one covering the other.
            mixed_rgb = (left_rgb[overlap] * right_rgb[overlap]) // 255
            output_rgb[overlap] = mixed_rgb
            output_alpha[overlap] = left_alpha[overlap] + right_alpha[overlap] - (
                left_alpha[overlap] * right_alpha[overlap] // 255
            )

        blended = pygame.Surface(canvas_size, pygame.SRCALPHA)
        blended_rgb = pygame.surfarray.pixels3d(blended)
        blended_rgb[:] = output_rgb.astype("uint8")
        del blended_rgb
        blended_alpha = pygame.surfarray.pixels_alpha(blended)
        blended_alpha[:] = output_alpha.astype("uint8")
        del blended_alpha
        return blended
