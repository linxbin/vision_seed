import math
import random

import pygame
import pygame.surfarray

from core.asset_loader import load_image_if_exists, project_path


class EyeFindPatternService:
    PATTERN_IDS = (
        "star",
        "cat",
        "butterfly",
        "moon",
        "fish",
        "rocket",
        "leaf",
        "flower",
        "apple",
        "kite",
        "crown",
        "shell",
        "heart",
        "mushroom",
    )
    PATTERN_COLORS = (
        (255, 214, 140, 255),
        (154, 227, 168, 255),
        (160, 205, 255, 255),
        (252, 174, 174, 255),
        (198, 166, 255, 255),
        (255, 189, 118, 255),
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
        dark = (50, 58, 72, 255)
        stem = (104, 152, 88, 255)

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
            pygame.draw.circle(surf, dark, (cx - 16, cy + 8), 4)
            pygame.draw.circle(surf, dark, (cx + 16, cy + 8), 4)
            pygame.draw.line(surf, dark, (cx - 6, cy + 22), (cx + 6, cy + 22), 2)
        elif pattern_id == "butterfly":
            pygame.draw.ellipse(surf, color, pygame.Rect(cx - 56, cy - 34, 46, 54))
            pygame.draw.ellipse(surf, color, pygame.Rect(cx + 10, cy - 34, 46, 54))
            pygame.draw.ellipse(surf, color, pygame.Rect(cx - 50, cy + 6, 40, 48))
            pygame.draw.ellipse(surf, color, pygame.Rect(cx + 10, cy + 6, 40, 48))
            pygame.draw.rect(surf, dark, pygame.Rect(cx - 5, cy - 24, 10, 68), border_radius=6)
            pygame.draw.line(surf, dark, (cx - 2, cy - 26), (cx - 10, cy - 40), 2)
            pygame.draw.line(surf, dark, (cx + 2, cy - 26), (cx + 10, cy - 40), 2)
        elif pattern_id == "moon":
            pygame.draw.circle(surf, color, (cx + 6, cy), int(size * 0.28))
            pygame.draw.circle(surf, (0, 0, 0, 0), (cx + 18, cy - 2), int(size * 0.22))
            pygame.draw.circle(surf, (255, 255, 255, 100), (cx - 8, cy - 14), int(size * 0.07))
        elif pattern_id == "fish":
            pygame.draw.ellipse(surf, color, pygame.Rect(cx - 44, cy - 24, 78, 48))
            pygame.draw.polygon(surf, color, [(cx + 28, cy), (cx + 58, cy - 22), (cx + 58, cy + 22)])
            pygame.draw.polygon(surf, color, [(cx - 4, cy), (cx + 14, cy - 18), (cx + 18, cy)])
            pygame.draw.circle(surf, dark, (cx - 20, cy - 4), 4)
        elif pattern_id == "rocket":
            pygame.draw.ellipse(surf, color, pygame.Rect(cx - 18, cy - 42, 36, 76))
            pygame.draw.polygon(surf, color, [(cx, cy - 56), (cx - 18, cy - 20), (cx + 18, cy - 20)])
            pygame.draw.polygon(surf, color, [(cx - 18, cy + 6), (cx - 40, cy + 30), (cx - 16, cy + 30)])
            pygame.draw.polygon(surf, color, [(cx + 18, cy + 6), (cx + 40, cy + 30), (cx + 16, cy + 30)])
            pygame.draw.circle(surf, (232, 244, 255, 220), (cx, cy - 8), 10)
            pygame.draw.polygon(surf, (255, 180, 84, 255), [(cx, cy + 42), (cx - 12, cy + 20), (cx + 12, cy + 20)])
        elif pattern_id == "leaf":
            pygame.draw.ellipse(surf, color, pygame.Rect(cx - 34, cy - 44, 68, 88))
            pygame.draw.line(surf, stem, (cx - 2, cy + 38), (cx + 6, cy - 34), 4)
            pygame.draw.line(surf, stem, (cx + 2, cy - 6), (cx - 18, cy - 22), 2)
            pygame.draw.line(surf, stem, (cx + 6, cy + 10), (cx + 22, cy - 6), 2)
        elif pattern_id == "flower":
            petal_r = int(size * 0.14)
            offsets = ((0, -28), (26, -8), (16, 24), (-16, 24), (-26, -8))
            for ox, oy in offsets:
                pygame.draw.circle(surf, color, (cx + ox, cy + oy), petal_r)
            pygame.draw.circle(surf, (255, 225, 122, 255), (cx, cy + 2), int(size * 0.11))
            pygame.draw.rect(surf, stem, pygame.Rect(cx - 3, cy + 18, 6, 36), border_radius=3)
            pygame.draw.ellipse(surf, (128, 188, 112, 255), pygame.Rect(cx - 26, cy + 24, 22, 12))
            pygame.draw.ellipse(surf, (128, 188, 112, 255), pygame.Rect(cx + 4, cy + 30, 22, 12))
        elif pattern_id == "apple":
            pygame.draw.circle(surf, color, (cx - 14, cy + 8), int(size * 0.2))
            pygame.draw.circle(surf, color, (cx + 14, cy + 8), int(size * 0.2))
            pygame.draw.polygon(surf, color, [(cx - 32, cy + 4), (cx, cy - 26), (cx + 32, cy + 4), (cx + 24, cy + 32), (cx - 24, cy + 32)])
            pygame.draw.line(surf, dark, (cx, cy - 28), (cx + 6, cy - 46), 4)
            pygame.draw.ellipse(surf, stem, pygame.Rect(cx + 6, cy - 48, 22, 12), 0)
            pygame.draw.circle(surf, (255, 255, 255, 70), (cx - 18, cy - 2), 8)
        elif pattern_id == "kite":
            pygame.draw.polygon(surf, color, [(cx, cy - 48), (cx + 34, cy), (cx, cy + 46), (cx - 34, cy)])
            pygame.draw.line(surf, (255, 255, 255, 180), (cx, cy - 48), (cx, cy + 46), 2)
            pygame.draw.line(surf, (255, 255, 255, 180), (cx - 34, cy), (cx + 34, cy), 2)
            pygame.draw.line(surf, dark, (cx, cy + 46), (cx + 6, cy + 82), 2)
            pygame.draw.polygon(surf, (255, 214, 140, 255), [(cx + 8, cy + 66), (cx + 18, cy + 74), (cx + 8, cy + 82)])
            pygame.draw.polygon(surf, (160, 205, 255, 255), [(cx - 2, cy + 78), (cx + 8, cy + 86), (cx - 2, cy + 94)])
        elif pattern_id == "crown":
            pygame.draw.polygon(surf, color, [(cx - 44, cy + 28), (cx - 32, cy - 12), (cx - 6, cy + 10), (cx + 2, cy - 26), (cx + 20, cy + 10), (cx + 44, cy - 8), (cx + 44, cy + 28)])
            pygame.draw.rect(surf, color, pygame.Rect(cx - 46, cy + 22, 92, 18), border_radius=6)
            for ox in (-28, 0, 28):
                pygame.draw.circle(surf, (255, 244, 190, 255), (cx + ox, cy + 6), 5)
        elif pattern_id == "shell":
            pygame.draw.arc(surf, color, pygame.Rect(cx - 44, cy - 6, 88, 72), math.pi, math.tau, 12)
            for shift in (-24, -8, 8, 24):
                pygame.draw.line(surf, color, (cx + shift, cy + 12), (cx + shift // 2, cy + 52), 6)
            pygame.draw.line(surf, color, (cx - 34, cy + 30), (cx + 34, cy + 30), 8)
        elif pattern_id == "heart":
            pygame.draw.circle(surf, color, (cx - 18, cy - 8), int(size * 0.16))
            pygame.draw.circle(surf, color, (cx + 18, cy - 8), int(size * 0.16))
            pygame.draw.polygon(surf, color, [(cx - 42, cy + 2), (cx, cy + 52), (cx + 42, cy + 2)])
        elif pattern_id == "mushroom":
            pygame.draw.ellipse(surf, color, pygame.Rect(cx - 44, cy - 42, 88, 46))
            pygame.draw.rect(surf, (244, 232, 214, 255), pygame.Rect(cx - 16, cy - 4, 32, 50), border_radius=12)
            for ox in (-22, 0, 22):
                pygame.draw.circle(surf, (255, 245, 235, 230), (cx + ox, cy - 18), 6)
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
