import random

import pygame


class SpotDifferenceBoardService:
    SHAPE_CIRCLE = "circle"
    SHAPE_SQUARE = "square"
    SHAPE_TRIANGLE = "triangle"
    SHAPE_DIAMOND = "diamond"
    SHAPE_STAR = "star"
    SHAPE_HEXAGON = "hexagon"
    SHAPE_PLUS = "plus"
    SHAPES = (
        SHAPE_CIRCLE,
        SHAPE_SQUARE,
        SHAPE_TRIANGLE,
        SHAPE_DIAMOND,
        SHAPE_STAR,
        SHAPE_HEXAGON,
        SHAPE_PLUS,
    )
    COLORS = ((246, 174, 112), (122, 190, 255), (162, 228, 168), (245, 210, 110))
    DIFF_SHAPE = "shape"
    DIFF_COLOR = "color"
    DIFF_SIZE = "size"
    DIFF_TYPES = (DIFF_SHAPE, DIFF_COLOR, DIFF_SIZE)

    def create_round(self, board_rect: pygame.Rect, diff_count: int = 2) -> dict:
        columns = 3
        rows = 2
        cell_w = board_rect.width // columns
        cell_h = board_rect.height // rows
        spots = []
        for row in range(rows):
            for col in range(columns):
                center = (
                    col * cell_w + cell_w // 2,
                    row * cell_h + cell_h // 2,
                )
                jitter_x = random.randint(-min(14, cell_w // 6), min(14, cell_w // 6))
                jitter_y = random.randint(-min(12, cell_h // 6), min(12, cell_h // 6))
                spots.append(
                    {
                        "center": (center[0] + jitter_x, center[1] + jitter_y),
                        "shape": random.choice(self.SHAPES),
                        "size": random.randint(34, 42),
                        "color": random.choice(self.COLORS),
                    }
                )

        diff_count = max(1, min(len(spots) - 1, int(diff_count)))
        diff_indices = random.sample(range(len(spots)), diff_count)
        right_spots = [dict(item) for item in spots]
        diff_details = []
        for diff_index in diff_indices:
            diff_type = random.choice(self.DIFF_TYPES)
            if diff_type == self.DIFF_SHAPE:
                original_shape = right_spots[diff_index]["shape"]
                candidates = [shape for shape in self.SHAPES if shape != original_shape]
                right_spots[diff_index]["shape"] = random.choice(candidates)
            elif diff_type == self.DIFF_COLOR:
                original_color = right_spots[diff_index]["color"]
                candidates = [color for color in self.COLORS if color != original_color]
                right_spots[diff_index]["color"] = random.choice(candidates)
            else:
                base_size = right_spots[diff_index]["size"]
                delta = random.choice((-16, -14, 14, 16))
                right_spots[diff_index]["size"] = max(20, min(60, base_size + delta))
            diff_details.append({"index": diff_index, "type": diff_type})
        return {
            "left": spots,
            "right": right_spots,
            "diff_indices": diff_indices,
            "diff_details": diff_details,
            "diff_index": diff_indices[0],
        }

    def draw_shape(self, surface, shape, center, size, color, outline_color=None, outline_width=0):
        cx, cy = center
        if outline_color and outline_width > 0:
            self.draw_shape(surface, shape, center, size + outline_width * 2, outline_color, outline_width=0)
        if shape == self.SHAPE_CIRCLE:
            pygame.draw.circle(surface, color, (int(cx), int(cy)), size // 2)
        elif shape == self.SHAPE_SQUARE:
            rect = pygame.Rect(0, 0, size, size)
            rect.center = (int(cx), int(cy))
            pygame.draw.rect(surface, color, rect, border_radius=8)
        elif shape == self.SHAPE_TRIANGLE:
            points = [
                (cx, cy - size // 2),
                (cx - size // 2, cy + size // 2),
                (cx + size // 2, cy + size // 2),
            ]
            pygame.draw.polygon(surface, color, points)
        elif shape == self.SHAPE_DIAMOND:
            points = [
                (cx, cy - size // 2),
                (cx - size // 2, cy),
                (cx, cy + size // 2),
                (cx + size // 2, cy),
            ]
            pygame.draw.polygon(surface, color, points)
        elif shape == self.SHAPE_STAR:
            outer = size // 2
            inner = max(10, size // 4)
            points = []
            for index in range(10):
                radius = outer if index % 2 == 0 else inner
                angle = -90 + index * 36
                radians = angle * 3.141592653589793 / 180.0
                points.append((cx + radius * pygame.math.Vector2(1, 0).rotate(angle).x, cy + radius * pygame.math.Vector2(1, 0).rotate(angle).y))
            pygame.draw.polygon(surface, color, points)
        elif shape == self.SHAPE_HEXAGON:
            points = []
            radius = size // 2
            for index in range(6):
                angle = 30 + index * 60
                vector = pygame.math.Vector2(radius, 0).rotate(angle)
                points.append((cx + vector.x, cy + vector.y))
            pygame.draw.polygon(surface, color, points)
        else:
            bar = max(8, size // 4)
            rect_h = pygame.Rect(0, 0, size, bar)
            rect_h.center = (int(cx), int(cy))
            rect_v = pygame.Rect(0, 0, bar, size)
            rect_v.center = (int(cx), int(cy))
            pygame.draw.rect(surface, color, rect_h, border_radius=bar // 2)
            pygame.draw.rect(surface, color, rect_v, border_radius=bar // 2)

    def hit_test_shape(self, shape, center, size, point):
        local_size = size + 18
        surface = pygame.Surface((local_size, local_size), pygame.SRCALPHA)
        local_center = (local_size // 2, local_size // 2)
        self.draw_shape(surface, shape, local_center, size, (255, 255, 255))
        local_x = int(point[0] - center[0] + local_center[0])
        local_y = int(point[1] - center[1] + local_center[1])
        if not (0 <= local_x < local_size and 0 <= local_y < local_size):
            return False
        mask = pygame.mask.from_surface(surface)
        return bool(mask.get_at((local_x, local_y)))
