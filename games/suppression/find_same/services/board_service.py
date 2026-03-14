import random

import pygame

from games.simultaneous.spot_difference.services.board_service import SpotDifferenceBoardService


class FindSameBoardService(SpotDifferenceBoardService):
    def create_round(self, board_rect: pygame.Rect, match_count: int = 2) -> dict:
        columns = 3
        rows = 2
        cell_w = board_rect.width // columns
        cell_h = board_rect.height // rows

        right_spots = []
        for row in range(rows):
            for col in range(columns):
                center = (col * cell_w + cell_w // 2, row * cell_h + cell_h // 2)
                jitter_x = random.randint(-min(14, cell_w // 6), min(14, cell_w // 6))
                jitter_y = random.randint(-min(12, cell_h // 6), min(12, cell_h // 6))
                right_spots.append(
                    {
                        "center": (center[0] + jitter_x, center[1] + jitter_y),
                        "shape": random.choice(self.SHAPES),
                        "size": random.randint(34, 42),
                        "color": random.choice(self.COLORS),
                    }
                )

        match_count = max(2, min(4, int(match_count)))
        match_indices = sorted(random.sample(range(len(right_spots)), match_count))
        ref_positions = [
            (board_rect.width // 2, board_rect.height // 4),
            (board_rect.width // 3, board_rect.height // 2),
            (board_rect.width * 2 // 3, board_rect.height // 2),
            (board_rect.width // 2, board_rect.height * 3 // 4),
        ]

        refs = []
        signatures = []
        for idx in range(match_count):
            reference = {
                "center": ref_positions[idx],
                "shape": random.choice(self.SHAPES),
                "size": random.randint(34, 42),
                "color": random.choice(self.COLORS),
            }
            refs.append(reference)
            signatures.append((reference["shape"], reference["color"], reference["size"]))

        for ref_index, target_index in enumerate(match_indices):
            shape, color, size = signatures[ref_index]
            right_spots[target_index]["shape"] = shape
            right_spots[target_index]["color"] = color
            right_spots[target_index]["size"] = size

        for idx, item in enumerate(right_spots):
            if idx in match_indices:
                continue
            while (item["shape"], item["color"], item["size"]) in signatures:
                mutate = random.choice(("shape", "color", "size"))
                if mutate == "shape":
                    item["shape"] = random.choice([shape for shape in self.SHAPES if shape != item["shape"]])
                elif mutate == "color":
                    item["color"] = random.choice([color for color in self.COLORS if color != item["color"]])
                else:
                    item["size"] = random.randint(26, 50)
        return {
            "left": refs,
            "right": right_spots,
            "match_indices": match_indices,
        }

