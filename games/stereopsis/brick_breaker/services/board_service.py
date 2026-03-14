import random


class BrickBreakerBoardService:
    def create_round(self, play_area):
        bricks = []
        brick_w = 84
        brick_h = 28
        start_x = play_area.left + 34
        start_y = play_area.top + 42
        for row in range(3):
            for col in range(6):
                bricks.append(
                    {
                        "rect": [start_x + col * (brick_w + 8), start_y + row * (brick_h + 10), brick_w, brick_h],
                        "depth": row,
                    }
                )
        return {
            "paddle_x": play_area.centerx,
            "paddle_width": 132,
            "ball": [play_area.centerx, play_area.bottom - 80],
            "velocity": [4, -5],
            "bricks": bricks,
        }

