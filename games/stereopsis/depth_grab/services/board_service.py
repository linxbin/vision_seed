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

    def _fallback_anchors(self, play_area):
        return [
            (play_area.left + 120, play_area.top + 82),
            (play_area.centerx, play_area.top + 58),
            (play_area.right - 130, play_area.top + 96),
            (play_area.left + 150, play_area.bottom - 110),
            (play_area.centerx - 34, play_area.bottom - 78),
            (play_area.right - 144, play_area.bottom - 122),
        ]

    def _random_centers(self, play_area, radii, layer_offsets):
        left = play_area.left + 82
        right = play_area.right - 82
        top = play_area.top + 68
        bottom = play_area.bottom - 68
        for _ in range(40):
            placed = []
            success = True
            for radius, layer_offset in zip(radii, layer_offsets):
                found = None
                min_x = left + radius
                max_x = right - radius
                min_y = top + radius - min(0, layer_offset)
                max_y = bottom - radius - max(0, layer_offset)
                for _ in range(160):
                    candidate = (
                        random.randint(min_x, max_x),
                        random.randint(min_y, max_y),
                    )
                    if all(
                        math.hypot(candidate[0] - px, candidate[1] - py) >= (radius + pr + 82)
                        for (px, py), pr in placed
                    ):
                        found = candidate
                        break
                if found is None:
                    success = False
                    break
                placed.append((found, radius))
            if success:
                return [center for center, _radius in placed]
        return self._fallback_anchors(play_area)

    def create_round(self, play_area, stage_index):
        target_count = 6
        correct_index = random.randrange(target_count)
        remaining_ranks = [1, 2, 3, 4, 5]
        random.shuffle(remaining_ranks)
        depth_ranks = []
        for idx in range(target_count):
            depth_ranks.append(0 if idx == correct_index else remaining_ranks.pop())
        radii = [int(30 * (1.58 - depth_rank * 0.14)) for depth_rank in depth_ranks]
        layer_offsets = [(-42, -24, -8, 10, 28, 44)[depth_rank] for depth_rank in depth_ranks]
        anchors = self._random_centers(play_area, radii, layer_offsets)
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
