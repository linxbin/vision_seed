import random


class SnakeBoardService:
    CELL = 28

    def create_round(self, play_area):
        cols = max(12, play_area.width // self.CELL)
        rows = max(10, play_area.height // self.CELL)
        start = (cols // 2, rows // 2)
        return {
            "cols": cols,
            "rows": rows,
            "snake": [start, (start[0] - 1, start[1]), (start[0] - 2, start[1])],
            "direction": (1, 0),
            "pending_direction": (1, 0),
            "food": self._spawn_food(cols, rows, [start, (start[0] - 1, start[1]), (start[0] - 2, start[1])]),
        }

    def _spawn_food(self, cols, rows, snake):
        cells = [(x, y) for x in range(cols) for y in range(rows) if (x, y) not in snake]
        return random.choice(cells)

    def stage_label_key(self, progress):
        return "snake_focus.stage.warmup" if progress < 0.34 else "snake_focus.stage.steady" if progress < 0.67 else "snake_focus.stage.challenge"

    def goal_label_key(self, progress):
        return "snake_focus.goal.warmup" if progress < 0.34 else "snake_focus.goal.steady" if progress < 0.67 else "snake_focus.goal.challenge"

