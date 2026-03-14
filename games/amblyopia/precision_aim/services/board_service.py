import math
import random


class PrecisionAimBoardService:
    def create_round(self, play_area, stage_index, difficulty_level, previous_anchor=None):
        anchor_center = None
        for _ in range(40):
            candidate = (
                random.randint(play_area.left + 92, play_area.right - 92),
                random.randint(play_area.top + 82, play_area.bottom - 82),
            )
            if previous_anchor is None or math.hypot(candidate[0] - previous_anchor[0], candidate[1] - previous_anchor[1]) >= 130:
                anchor_center = candidate
                break
        if anchor_center is None:
            anchor_center = (
                random.randint(play_area.left + 92, play_area.right - 92),
                random.randint(play_area.top + 82, play_area.bottom - 82),
            )
        difficulty_offset = max(0, int(difficulty_level) - 3) * 2
        if stage_index == 0:
            base_radius = max(30, 54 - difficulty_offset)
        elif stage_index == 1:
            base_radius = max(22, 42 - difficulty_offset)
        else:
            base_radius = max(16, 34 - difficulty_offset)
        return {
            "anchor_center": anchor_center,
            "target_center": anchor_center,
            "aim_center": [play_area.centerx, play_area.centery],
            "base_radius": base_radius,
            "current_radius": base_radius,
            "challenge_shift": random.uniform(0.0, math.pi * 2),
            "stage_index": stage_index,
        }

    def stage_label_key(self, stage_index):
        return (
            "precision_aim.stage.warmup",
            "precision_aim.stage.steady",
            "precision_aim.stage.challenge",
        )[stage_index]

    def goal_label_key(self, stage_index):
        return (
            "precision_aim.goal.warmup",
            "precision_aim.goal.steady",
            "precision_aim.goal.challenge",
        )[stage_index]
