import random


class FusionTetrisBoardService:
    SHAPES = (
        [(0, 0), (1, 0), (0, 1), (1, 1)],
        [(0, 0), (1, 0), (2, 0), (1, 1)],
        [(0, 0), (1, 0), (1, 1), (2, 1)],
    )

    def create_round(self, cols=8, rows=14):
        return {
            "cols": cols,
            "rows": rows,
            "stack": [],
            "piece": random.choice(self.SHAPES),
            "piece_x": cols // 2 - 1,
            "piece_y": 0,
        }

