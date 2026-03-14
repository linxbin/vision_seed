import random


class RedBlueCatchBoardService:
    COLORS = ("red", "blue")

    def create_round(self, play_area, mode):
        color = random.choice(self.COLORS)
        return {
            "ball_x": random.randint(play_area.left + 40, play_area.right - 40),
            "ball_y": play_area.top + 24,
            "speed": random.randint(6, 9),
            "target_color": color,
            "ball_color": color if random.random() < 0.72 else ("blue" if color == "red" else "red"),
            "basket_x": play_area.centerx,
            "basket_width": 128,
            "mode": mode,
        }

