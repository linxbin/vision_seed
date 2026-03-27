import math
import random


class PopNearestBoardService:
    DEPTH_LAYOUTS = (
        {"rank": 0, "progress": 0.90, "radius": 42, "disparity": 38},
        {"rank": 1, "progress": 0.68, "radius": 42, "disparity": 28},
        {"rank": 2, "progress": 0.36, "radius": 42, "disparity": 18},
        {"rank": 3, "progress": 0.08, "radius": 42, "disparity": 10},
    )
    BASE_HORIZONTAL_FACTORS = (0.14, 0.38, 0.62, 0.86)
    HORIZONTAL_JITTER = 0.035

    def __init__(self, seed=None):
        self._random = random.Random(seed)

    def create_group(self, play_area, group_index):
        order = self._build_horizontal_order()
        balloons = []
        for idx, spec in enumerate(self.DEPTH_LAYOUTS):
            center = self._project_center(play_area, order[idx], spec["progress"])
            balloons.append(
                {
                    "depth_rank": spec["rank"],
                    "base_center": center,
                    "radius": spec["radius"],
                    "disparity": spec["disparity"],
                    "float_phase": self._random.uniform(0.0, math.tau),
                    "float_speed": 0.68 + idx * 0.1,
                    "float_amplitude": 4,
                    "popped": False,
                }
            )
        return {"group_index": group_index, "balloons": balloons}

    def _build_horizontal_order(self):
        factors = []
        for base in self.BASE_HORIZONTAL_FACTORS:
            jitter = self._random.uniform(-self.HORIZONTAL_JITTER, self.HORIZONTAL_JITTER)
            factors.append(min(0.9, max(0.1, base + jitter)))
        self._random.shuffle(factors)
        return factors

    def _project_center(self, play_area, horizontal_factor, progress):
        width = play_area.width * (0.58 + progress * 0.22)
        x = int(play_area.centerx - width / 2 + width * horizontal_factor)
        top_padding = 54
        bottom_padding = 96
        usable_height = max(120, play_area.height - top_padding - bottom_padding)
        y = int(play_area.top + top_padding + (1.0 - progress) * usable_height)
        return x, y

    def display_center(self, balloon, elapsed):
        drift_y = math.sin(elapsed * balloon["float_speed"] + balloon["float_phase"]) * balloon["float_amplitude"]
        drift_x = math.cos(elapsed * 0.55 + balloon["float_phase"] * 0.7) * 3
        return (
            int(balloon["base_center"][0] + drift_x),
            int(balloon["base_center"][1] + drift_y),
        )

    def current_target_rank(self, balloons):
        remaining = [balloon["depth_rank"] for balloon in balloons if not balloon.get("popped")]
        return min(remaining) if remaining else None

    def hit_test(self, balloons, pos, elapsed):
        for idx, balloon in enumerate(balloons):
            if balloon.get("popped"):
                continue
            center = self.display_center(balloon, elapsed)
            radius = balloon["radius"] + 6
            disparity = max(6, balloon["disparity"] // 2)
            if (
                math.hypot(pos[0] - (center[0] - disparity), pos[1] - center[1]) <= radius
                or math.hypot(pos[0] - (center[0] + disparity), pos[1] - center[1]) <= radius
            ):
                return idx
        return None
