import random

import pygame


class SpotDifferenceBoardService:
    SHAPE_CIRCLE = "circle"
    SHAPE_SQUARE = "square"
    SHAPE_TRIANGLE = "triangle"
    SHAPES = (SHAPE_CIRCLE, SHAPE_SQUARE, SHAPE_TRIANGLE)
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
                delta = random.choice((-10, -8, 8, 10))
                right_spots[diff_index]["size"] = max(26, min(54, base_size + delta))
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
        else:
            points = [
                (cx, cy - size // 2),
                (cx - size // 2, cy + size // 2),
                (cx + size // 2, cy + size // 2),
            ]
            pygame.draw.polygon(surface, color, points)
