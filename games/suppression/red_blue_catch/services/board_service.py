import random


class RedBlueCatchBoardService:
    COLORS = ("red", "blue")

    def _ball_speed(self, stage_index):
        if stage_index == 0:
            return random.uniform(7.6, 9.2)
        if stage_index == 1:
            return random.uniform(8.8, 10.4)
        return random.uniform(10.2, 11.8)

    def create_ball(self, play_area, stage_index, occupied_x=None):
        occupied_x = occupied_x or []
        attempts = 0
        ball_x = play_area.centerx
        while attempts < 12:
            candidate = random.randint(play_area.left + 44, play_area.right - 44)
            if all(abs(candidate - other) >= 68 for other in occupied_x):
                ball_x = candidate
                break
            attempts += 1
        lane = random.randint(0, 3)
        return {
            "x": ball_x,
            "y": play_area.top + 24 - lane * 52,
            "speed": self._ball_speed(stage_index),
            "color": random.choice(self.COLORS),
        }

    def create_round(self, play_area, mode, stage_index):
        ball_count = random.randint(2, 3) if stage_index < 2 else random.randint(3, 4)
        balls = []
        for _ in range(ball_count):
            balls.append(self.create_ball(play_area, stage_index, [ball["x"] for ball in balls]))
        return {
            "balls": balls,
            "basket_x": play_area.centerx,
            "basket_width": 128,
            "mode": mode,
            "stage_index": stage_index,
        }
