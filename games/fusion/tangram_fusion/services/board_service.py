import random

import pygame

from games.common.anaglyph import FILTER_LR


class TangramFusionBoardService:
    PIECE_ORDER = (
        "large_triangle",
        "large_triangle",
        "medium_triangle",
        "square",
        "small_triangle",
        "small_triangle",
        "parallelogram",
    )

    CANONICAL_PIECES = {
        "large_triangle": [(10, 90), (90, 90), (10, 10)],
        "medium_triangle": [(16, 84), (84, 84), (16, 16)],
        "small_triangle": [(24, 76), (76, 76), (24, 24)],
        "square": [(24, 24), (76, 24), (76, 76), (24, 76)],
        "parallelogram": [(18, 70), (70, 70), (82, 30), (30, 30)],
    }

    TEMPLATES = [
        {
            "id": "letter_a",
            "stage": 0,
            "slots": [
                {"piece_type": "large_triangle", "polygon": [(18, 74), (36, 56), (36, 74)]},
                {"piece_type": "large_triangle", "polygon": [(64, 56), (82, 74), (64, 74)]},
                {"piece_type": "medium_triangle", "polygon": [(42, 34), (58, 34), (50, 22)]},
                {"piece_type": "square", "polygon": [(44, 56), (56, 56), (56, 68), (44, 68)]},
                {"piece_type": "small_triangle", "polygon": [(34, 48), (42, 40), (42, 48)]},
                {"piece_type": "small_triangle", "polygon": [(58, 40), (66, 48), (58, 48)]},
                {"piece_type": "parallelogram", "polygon": [(34, 76), (52, 76), (60, 88), (42, 88)]},
            ],
            "missing_indices": [2, 3, 4, 6],
        },
        {
            "id": "letter_c",
            "stage": 0,
            "slots": [
                {"piece_type": "large_triangle", "polygon": [(22, 34), (38, 34), (22, 50)]},
                {"piece_type": "large_triangle", "polygon": [(22, 52), (38, 68), (22, 68)]},
                {"piece_type": "medium_triangle", "polygon": [(46, 26), (60, 26), (46, 40)]},
                {"piece_type": "square", "polygon": [(62, 28), (72, 28), (72, 38), (62, 38)]},
                {"piece_type": "small_triangle", "polygon": [(74, 30), (84, 40), (74, 40)]},
                {"piece_type": "small_triangle", "polygon": [(74, 60), (84, 70), (74, 70)]},
                {"piece_type": "parallelogram", "polygon": [(42, 72), (58, 72), (66, 82), (50, 82)]},
            ],
            "missing_indices": [2, 3, 5, 6],
        },
        {
            "id": "hexagon",
            "stage": 0,
            "slots": [
                {"piece_type": "large_triangle", "polygon": [(26, 48), (42, 32), (42, 48)]},
                {"piece_type": "large_triangle", "polygon": [(58, 32), (82, 56), (58, 56)]},
                {"piece_type": "medium_triangle", "polygon": [(42, 32), (58, 32), (50, 46)]},
                {"piece_type": "square", "polygon": [(38, 58), (50, 58), (50, 70), (38, 70)]},
                {"piece_type": "small_triangle", "polygon": [(14, 52), (24, 42), (24, 52)]},
                {"piece_type": "small_triangle", "polygon": [(54, 72), (64, 82), (54, 82)]},
                {"piece_type": "parallelogram", "polygon": [(50, 58), (66, 58), (76, 72), (60, 72)]},
            ],
            "missing_indices": [1, 3, 4, 6],
        },
        {
            "id": "sword",
            "stage": 1,
            "slots": [
                {"piece_type": "large_triangle", "polygon": [(44, 54), (62, 36), (62, 54)]},
                {"piece_type": "large_triangle", "polygon": [(44, 74), (62, 56), (62, 92)]},
                {"piece_type": "medium_triangle", "polygon": [(28, 44), (42, 44), (28, 58)]},
                {"piece_type": "square", "polygon": [(44, 20), (56, 20), (56, 32), (44, 32)]},
                {"piece_type": "small_triangle", "polygon": [(46, 2), (56, 12), (46, 12)]},
                {"piece_type": "small_triangle", "polygon": [(68, 18), (78, 28), (68, 28)]},
                {"piece_type": "parallelogram", "polygon": [(24, 80), (40, 80), (50, 94), (34, 94)]},
            ],
            "missing_indices": [0, 2, 3, 6],
        },
        {
            "id": "duck",
            "stage": 1,
            "slots": [
                {"piece_type": "large_triangle", "polygon": [(34, 66), (60, 66), (60, 92)]},
                {"piece_type": "large_triangle", "polygon": [(60, 66), (86, 92), (60, 92)]},
                {"piece_type": "medium_triangle", "polygon": [(58, 36), (72, 36), (58, 50)]},
                {"piece_type": "square", "polygon": [(46, 24), (58, 24), (58, 36), (46, 36)]},
                {"piece_type": "small_triangle", "polygon": [(26, 20), (38, 20), (38, 32)]},
                {"piece_type": "small_triangle", "polygon": [(24, 92), (34, 92), (24, 102)]},
                {"piece_type": "parallelogram", "polygon": [(26, 52), (44, 52), (56, 66), (38, 66)]},
            ],
            "missing_indices": [2, 3, 5, 6],
        },
        {
            "id": "chicken_ii",
            "stage": 1,
            "slots": [
                {"piece_type": "large_triangle", "polygon": [(56, 54), (84, 54), (56, 82)]},
                {"piece_type": "large_triangle", "polygon": [(62, 26), (84, 48), (62, 48)]},
                {"piece_type": "medium_triangle", "polygon": [(34, 36), (50, 36), (34, 52)]},
                {"piece_type": "square", "polygon": [(34, 52), (46, 52), (46, 64), (34, 64)]},
                {"piece_type": "small_triangle", "polygon": [(20, 82), (30, 82), (20, 92)]},
                {"piece_type": "small_triangle", "polygon": [(84, 42), (94, 52), (84, 52)]},
                {"piece_type": "parallelogram", "polygon": [(12, 62), (26, 62), (36, 74), (22, 74)]},
            ],
            "missing_indices": [1, 3, 4, 6],
        },
        {
            "id": "eagle_i",
            "stage": 2,
            "slots": [
                {"piece_type": "large_triangle", "polygon": [(10, 58), (38, 30), (38, 58)]},
                {"piece_type": "large_triangle", "polygon": [(62, 30), (90, 58), (62, 58)]},
                {"piece_type": "medium_triangle", "polygon": [(44, 24), (56, 24), (50, 36)]},
                {"piece_type": "square", "polygon": [(44, 58), (56, 58), (56, 70), (44, 70)]},
                {"piece_type": "small_triangle", "polygon": [(38, 40), (46, 48), (38, 48)]},
                {"piece_type": "small_triangle", "polygon": [(54, 40), (62, 48), (54, 48)]},
                {"piece_type": "parallelogram", "polygon": [(42, 72), (58, 72), (66, 86), (50, 86)]},
            ],
            "missing_indices": [2, 3, 5, 6],
        },
        {
            "id": "cottage_iii",
            "stage": 2,
            "slots": [
                {"piece_type": "large_triangle", "polygon": [(52, 44), (84, 76), (52, 76)]},
                {"piece_type": "large_triangle", "polygon": [(34, 76), (66, 76), (34, 108)]},
                {"piece_type": "medium_triangle", "polygon": [(66, 76), (84, 94), (66, 94)]},
                {"piece_type": "square", "polygon": [(38, 18), (54, 18), (54, 34), (38, 34)]},
                {"piece_type": "small_triangle", "polygon": [(54, 34), (66, 46), (54, 46)]},
                {"piece_type": "small_triangle", "polygon": [(22, 62), (34, 62), (22, 74)]},
                {"piece_type": "parallelogram", "polygon": [(18, 46), (40, 46), (54, 62), (32, 62)]},
            ],
            "missing_indices": [1, 3, 5, 6],
        },
    ]

    def __init__(self):
        self.validate_templates()

    def create_round(self, stage_index, filter_direction=FILTER_LR):
        candidates = [template for template in self.TEMPLATES if template["stage"] <= stage_index]
        template = random.choice(candidates)
        missing_index = random.choice(template["missing_indices"])
        missing_slot = template["slots"][missing_index]
        slot_sides = self._build_slot_sides()
        options = self._build_options(missing_slot, stage_index)
        return {
            "template_id": template["id"],
            "template": template,
            "missing_index": missing_index,
            "options": options,
            "correct_option": next(index for index, option in enumerate(options) if option["piece_type"] == missing_slot["piece_type"]),
            "stage_index": stage_index,
            "slot_sides": slot_sides,
            "filter_direction": filter_direction,
        }

    def _build_slot_sides(self):
        sides = ["left"] * 3 + ["right"] * 4
        random.shuffle(sides)
        return sides

    def _build_options(self, missing_slot, stage_index):
        piece_type = missing_slot["piece_type"]
        pool = self._option_pool(piece_type, stage_index)
        options = []
        for candidate_type in pool:
            polygon = (
                [tuple(point) for point in missing_slot["polygon"]]
                if candidate_type == piece_type
                else self._fit_piece_to_slot(candidate_type, missing_slot["polygon"])
            )
            options.append({"piece_type": candidate_type, "polygon": polygon})
        random.shuffle(options)
        return options

    def _option_pool(self, piece_type, stage_index):
        if piece_type == "large_triangle":
            pool = ["large_triangle", "medium_triangle", "parallelogram"] if stage_index == 0 else ["large_triangle", "medium_triangle", "square"]
        elif piece_type == "medium_triangle":
            pool = ["medium_triangle", "small_triangle", "square"] if stage_index == 0 else ["medium_triangle", "large_triangle", "parallelogram"]
        elif piece_type == "small_triangle":
            pool = ["small_triangle", "medium_triangle", "square"] if stage_index == 0 else ["small_triangle", "parallelogram", "square"]
        elif piece_type == "square":
            pool = ["square", "medium_triangle", "parallelogram"] if stage_index == 0 else ["square", "small_triangle", "large_triangle"]
        else:
            pool = ["parallelogram", "square", "medium_triangle"] if stage_index == 0 else ["parallelogram", "large_triangle", "small_triangle"]
        return pool

    def _fit_piece_to_slot(self, piece_type, slot_polygon):
        source = self.CANONICAL_PIECES[piece_type]
        source_width, source_height, source_min_x, source_min_y = self._bounds(source)
        slot_width, slot_height, slot_min_x, slot_min_y = self._bounds(slot_polygon)
        scale = min(slot_width / max(1.0, source_width), slot_height / max(1.0, source_height))
        offset_x = slot_min_x + (slot_width - source_width * scale) / 2 - source_min_x * scale
        offset_y = slot_min_y + (slot_height - source_height * scale) / 2 - source_min_y * scale
        return [(int(round(offset_x + x * scale)), int(round(offset_y + y * scale))) for x, y in source]

    @staticmethod
    def _bounds(polygon):
        xs = [point[0] for point in polygon]
        ys = [point[1] for point in polygon]
        min_x, max_x = min(xs), max(xs)
        min_y, max_y = min(ys), max(ys)
        return max_x - min_x, max_y - min_y, min_x, min_y

    def stage_label_key(self, stage_index):
        return (
            "tangram_fusion.stage.warmup",
            "tangram_fusion.stage.steady",
            "tangram_fusion.stage.challenge",
        )[stage_index]

    def guide_alpha(self, stage_index):
        return (144, 92, 52)[stage_index]

    def color_for_side(self, side, filter_direction):
        if filter_direction == FILTER_LR:
            return (255, 0, 0) if side == "left" else (0, 0, 255)
        return (0, 0, 255) if side == "left" else (255, 0, 0)

    @classmethod
    def _polygons_overlap(cls, first, second):
        def inset(points, scale=0.9):
            center_x = sum(point[0] for point in points) / len(points)
            center_y = sum(point[1] for point in points) / len(points)
            return [(center_x + (x - center_x) * scale, center_y + (y - center_y) * scale) for x, y in points]

        shrunk_first = inset(first)
        shrunk_second = inset(second)
        xs = [point[0] for point in shrunk_first + shrunk_second]
        ys = [point[1] for point in shrunk_first + shrunk_second]
        width = max(xs) - min(xs) + 6
        height = max(ys) - min(ys) + 6
        offset_x = 2 - min(xs)
        offset_y = 2 - min(ys)
        first_surface = pygame.Surface((width, height), pygame.SRCALPHA)
        second_surface = pygame.Surface((width, height), pygame.SRCALPHA)
        first_points = [(int(round(x + offset_x)), int(round(y + offset_y))) for x, y in shrunk_first]
        second_points = [(int(round(x + offset_x)), int(round(y + offset_y))) for x, y in shrunk_second]
        pygame.draw.polygon(first_surface, (255, 255, 255, 255), first_points)
        pygame.draw.polygon(second_surface, (255, 255, 255, 255), second_points)
        first_alpha = pygame.surfarray.array_alpha(first_surface)
        second_alpha = pygame.surfarray.array_alpha(second_surface)
        return bool(((first_alpha > 0) & (second_alpha > 0)).any())

    @classmethod
    def validate_templates(cls):
        for template in cls.TEMPLATES:
            slot_types = [slot["piece_type"] for slot in template["slots"]]
            if tuple(slot_types) != cls.PIECE_ORDER:
                raise ValueError(f"Tangram template '{template['id']}' does not keep the required tangram piece order")
            slots = template["slots"]
            for index in range(len(slots)):
                first = slots[index]["polygon"]
                for other_index in range(index + 1, len(slots)):
                    second = slots[other_index]["polygon"]
                    if cls._polygons_overlap(first, second):
                        raise ValueError(f"Tangram template '{template['id']}' has overlapping slots: {index} and {other_index}")
