import math
import random

import pygame


class EyeFindPatternService:
    PATTERN_IDS = ("star", "cat", "butterfly", "moon")
    PATTERN_COLORS = (
        (255, 214, 140, 255),
        (154, 227, 168, 255),
        (160, 205, 255, 255),
        (252, 174, 174, 255),
    )
    RED_FILTER = (255, 102, 102, 204)
    BLUE_FILTER = (102, 102, 255, 204)

    def build_pattern_surface(self, pattern_id, size, color):
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
        overlay = pygame.Surface(base.get_size(), pygame.SRCALPHA)
        overlay.fill(color)
        result = base.copy()
        result.blit(overlay, (0, 0))
        return result
