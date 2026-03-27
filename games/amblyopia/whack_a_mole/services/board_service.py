import math
import random


class WhackAMoleBoardService:
    def create_round(self, play_area, stage_index, previous_index=None):
        cols = 3
        rows = 2
        holes = []
        for row in range(rows):
            for col in range(cols):
                holes.append(
                    (
                        play_area.left + (col + 0.5) * play_area.width / cols,
                        play_area.top + (row + 0.5) * play_area.height / rows,
                    )
                )
        choices = [idx for idx in range(len(holes)) if idx != previous_index]
        active_index = random.choice(choices or list(range(len(holes))))
        radius = 42 if stage_index == 0 else 34 if stage_index == 1 else 28
        return {
            "holes": holes,
            "active_index": active_index,
            "target_center": holes[active_index],
            "radius": radius,
            "stage_index": stage_index,
        }

    def stage_label_key(self, stage_index):
        return ("whack_a_mole.stage.warmup", "whack_a_mole.stage.steady", "whack_a_mole.stage.challenge")[stage_index]

    def goal_label_key(self, stage_index):
        return ("whack_a_mole.goal.warmup", "whack_a_mole.goal.steady", "whack_a_mole.goal.challenge")[stage_index]

    def hit_distance(self, point, center):
        return math.hypot(point[0] - center[0], point[1] - center[1])

