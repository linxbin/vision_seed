import random


class BrickBreakerBoardService:
    DEPTH_LEVELS = (0, 1, 2)

    def create_round(self, play_area):
        brick_count = 6
        brick_w = 72
        brick_h = 28
        gap = 20
        total_w = brick_count * brick_w + (brick_count - 1) * gap
        start_x = play_area.centerx - total_w // 2
        row_y = play_area.top + 56
        bricks = []
        for index in range(brick_count):
            bricks.append(
                {
                    "rect": [start_x + index * (brick_w + gap), row_y, brick_w, brick_h],
                    "depth": random.choice(self.DEPTH_LEVELS),
                }
            )
        attack_depth = random.choice([brick["depth"] for brick in bricks])
        return {
            "launcher_x": play_area.centerx,
            "attack_depth": attack_depth,
            "attack_ball": None,
            "bricks": bricks,
        }

    def create_attack_ball(self, play_area, launcher_x, attack_depth):
        return {
            "x": max(play_area.left + 24, min(play_area.right - 24, launcher_x)),
            "y": play_area.bottom - 34,
            "radius": 13,
            "speed": 11,
            "depth": attack_depth,
        }

    def refresh_bricks(self, play_area):
        fresh = self.create_round(play_area)
        fresh["launcher_x"] = play_area.centerx
        return fresh
