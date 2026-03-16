import math
import random


class DepthGrabBoardService:
    STAR_VARIANTS = (
        {"tips": 5, "rotation": -1.57},
        {"tips": 5, "rotation": -1.1},
        {"tips": 5, "rotation": -1.32},
        {"tips": 5, "rotation": -1.82},
        {"tips": 5, "rotation": -1.42},
        {"tips": 5, "rotation": -1.68},
    )
    NAKED_COLORS = (
        (255, 129, 146),
        (255, 194, 102),
        (122, 214, 160),
        (126, 186, 255),
        (182, 146, 255),
        (255, 154, 222),
    )

    def _fallback_anchors(self, play_area, display_radii, layer_offsets, bob_margins):
        columns = (0.17, 0.5, 0.83)
        rows = (0.28, 0.73)
        anchors = []
        for idx in range(len(display_radii)):
            display_radius = display_radii[idx]
            layer_offset = layer_offsets[idx]
            bob_margin = bob_margins[idx]
            col = columns[idx % len(columns)]
            row = rows[idx // len(columns)]
            min_x = play_area.left + display_radius + 8
            max_x = play_area.right - display_radius - 8
            min_y = play_area.top + display_radius + bob_margin - min(0, layer_offset)
            max_y = play_area.bottom - display_radius - bob_margin - max(0, layer_offset)
            center_x = int(play_area.left + play_area.width * col)
            center_y = int(play_area.top + play_area.height * row)
            anchors.append(
                (
                    max(min_x, min(max_x, center_x)),
                    max(min_y, min(max_y, center_y)),
                )
            )
        return anchors

    def _random_centers(self, play_area, radii, display_radii, layer_offsets, bob_margins):
        for _ in range(40):
            placed = []
            success = True
            for radius, display_radius, layer_offset, bob_margin in zip(radii, display_radii, layer_offsets, bob_margins):
                found = None
                min_x = play_area.left + display_radius + 8
                max_x = play_area.right - display_radius - 8
                min_y = play_area.top + display_radius + bob_margin - min(0, layer_offset)
                max_y = play_area.bottom - display_radius - bob_margin - max(0, layer_offset)
                if min_x > max_x or min_y > max_y:
                    success = False
                    break
                for _ in range(160):
                    candidate = (
                        random.randint(min_x, max_x),
                        random.randint(min_y, max_y),
                    )
                    if all(
                        math.hypot(candidate[0] - px, candidate[1] - py)
                        >= (
                            display_radius
                            + placed_display_radius
                            + 12
                            + 8
                            + abs(layer_offset - placed_layer_offset)
                            + bob_margin
                            + placed_bob_margin
                        )
                        for (px, py), placed_display_radius, placed_bob_margin, placed_layer_offset in placed
                    ):
                        found = candidate
                        break
                if found is None:
                    success = False
                    break
                placed.append((found, display_radius, bob_margin, layer_offset))
            if success:
                return [center for center, _display_radius, _bob_margin, _layer_offset in placed]
        return self._fallback_anchors(play_area, display_radii, layer_offsets, bob_margins)

    def create_round(self, play_area, stage_index):
        target_count = 6
        correct_index = random.randrange(target_count)
        remaining_ranks = [1, 2, 3, 4, 5]
        random.shuffle(remaining_ranks)
        depth_ranks = []
        for idx in range(target_count):
            depth_ranks.append(0 if idx == correct_index else remaining_ranks.pop())
        radii = [32 for _ in range(target_count)]
        layer_offsets = [(-42, -24, -8, 10, 28, 44)[depth_rank] for depth_rank in depth_ranks]
        display_radii = [radius + (6 if depth_rank == 0 else 3) for radius, depth_rank in zip(radii, depth_ranks)]
        bob_margins = [4 + depth_rank for depth_rank in depth_ranks]
        anchors = self._random_centers(play_area, radii, display_radii, layer_offsets, bob_margins)
        variants = random.sample(self.STAR_VARIANTS, k=target_count)
        colors = random.sample(self.NAKED_COLORS, k=target_count)
        targets = []
        for idx, center in enumerate(anchors):
            depth_rank = depth_ranks[idx]
            disparity = 34 - depth_rank * 4 + stage_index * 2
            layer_offset = layer_offsets[idx]
            targets.append(
                {
                    "center": center,
                    "radius": radii[idx],
                    "depth_rank": depth_rank,
                    "disparity": disparity,
                    "layer_offset": layer_offset,
                    "star_variant": variants[idx],
                    "naked_color": colors[idx],
                }
            )
        correct_index = next(idx for idx, target in enumerate(targets) if target["depth_rank"] == 0)
        return {"targets": targets, "correct_index": correct_index, "stage_index": stage_index}

    def stage_label_key(self, stage_index):
        return (
            "depth_grab.stage.warmup",
            "depth_grab.stage.steady",
            "depth_grab.stage.challenge",
        )[stage_index]

    def goal_label_key(self, stage_index):
        return (
            "depth_grab.goal.warmup",
            "depth_grab.goal.steady",
            "depth_grab.goal.challenge",
        )[stage_index]
