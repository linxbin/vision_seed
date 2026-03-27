import random


class FruitSliceBoardService:
    FRUIT_COLORS = ((238, 120, 96), (244, 196, 80), (116, 196, 122))

    def create_round(self, play_area):
        is_bomb = random.random() < 0.2
        return {
            "center": (
                random.randint(play_area.left + 70, play_area.right - 70),
                random.randint(play_area.top + 70, play_area.bottom - 70),
            ),
            "radius": random.randint(28, 42),
            "is_bomb": is_bomb,
            "color": (58, 58, 58) if is_bomb else random.choice(self.FRUIT_COLORS),
        }

