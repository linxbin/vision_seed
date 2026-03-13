import random

import pygame


class WeakEyeKeyBoardService:
    HEAD_SHAPES = ("round", "square", "diamond")
    KEY_COLORS = (
        (244, 196, 102),
        (132, 192, 255),
        (168, 224, 172),
    )

    def create_round(self, board_rect, clue_rect, stage_index):
        key_count = (6, 9, 12)[stage_index]
        target_shape = random.choice(self.HEAD_SHAPES)
        target_teeth = random.choice(((1, 3), (2, 1), (3, 2), (2, 4)))
        target_color = random.choice(self.KEY_COLORS)
        clue_mode = ("full", "shape_only", "teeth_only")[stage_index]
        positions = self._sample_positions(board_rect, key_count)
        target_index = random.randrange(key_count)
        keys = []
        for index in range(key_count):
            shape = random.choice(self.HEAD_SHAPES)
            teeth = random.choice(((1, 3), (2, 1), (3, 2), (2, 4)))
            color = random.choice(self.KEY_COLORS)
            if index == target_index:
                shape = target_shape
                teeth = target_teeth
                color = target_color
            elif stage_index >= 1:
                if random.random() < 0.5:
                    shape = target_shape
                else:
                    teeth = target_teeth
            keys.append(
                {
                    "rect": pygame.Rect(positions[index][0], positions[index][1], 74, 36),
                    "shape": shape,
                    "teeth": teeth,
                    "color": color,
                }
            )
        target_item = keys[target_index]
        clue = {
            "shape": target_item["shape"],
            "teeth": target_item["teeth"],
            "color": target_item["color"],
            "mode": clue_mode,
            "rect": pygame.Rect(clue_rect.x + 18, clue_rect.y + 70, clue_rect.width - 36, 92),
        }
        return {
            "keys": keys,
            "target_index": target_index,
            "clue": clue,
            "stage_index": stage_index,
        }

    def stage_label_key(self, stage_index):
        return (
            "weak_eye_key.stage.warmup",
            "weak_eye_key.stage.steady",
            "weak_eye_key.stage.challenge",
        )[stage_index]

    def goal_label_key(self, stage_index):
        return (
            "weak_eye_key.goal.warmup",
            "weak_eye_key.goal.steady",
            "weak_eye_key.goal.challenge",
        )[stage_index]

    def is_target_hit(self, round_data, pos):
        for index, item in enumerate(round_data["keys"]):
            if item["rect"].collidepoint(pos):
                return index == round_data["target_index"], index
        return None, None

    def _sample_positions(self, board_rect, count):
        positions = []
        attempts = 0
        while len(positions) < count and attempts < 400:
            attempts += 1
            rect = pygame.Rect(
                random.randint(board_rect.left + 20, board_rect.right - 94),
                random.randint(board_rect.top + 24, board_rect.bottom - 58),
                74,
                36,
            )
            if any(rect.colliderect(existing.inflate(18, 14)) for existing in positions):
                continue
            positions.append(rect)
        return [(rect.x, rect.y) for rect in positions]
