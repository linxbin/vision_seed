import random


class FroggerBoardService:
    def create_round(self, play_area):
        lanes = []
        lane_height = 58
        for idx in range(4):
            lanes.append(
                {
                    "y": play_area.bottom - 90 - idx * lane_height,
                    "direction": -1 if idx % 2 == 0 else 1,
                    "cars": [[play_area.left + 120 + idx * 80, play_area.bottom - 90 - idx * lane_height], [play_area.left + 420 + idx * 60, play_area.bottom - 90 - idx * lane_height]],
                }
            )
        return {"frog": [play_area.centerx, play_area.bottom - 28], "lanes": lanes}

