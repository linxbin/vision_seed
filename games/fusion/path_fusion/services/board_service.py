import random


class PathFusionBoardService:
    def create_round(self):
        options = [
            {"left": "up-right", "right": "right-down", "target": 0},
            {"left": "up-left", "right": "left-down", "target": 1},
            {"left": "up-right", "right": "right-right", "target": 2},
        ]
        return random.choice(options)

