class FroggerScoringService:
    def __init__(self):
        self.reset()

    def reset(self):
        self.score = 0
        self.safe_crosses = 0
        self.fall_count = 0
        self.moves = 0
        self.safe_moves = 0

    def on_move(self):
        self.moves += 1

    def on_safe_move(self):
        self.safe_moves += 1

    def on_cross(self):
        self.safe_crosses += 1
        self.score += 18

    def on_fail(self):
        self.fall_count += 1

    def accuracy(self):
        return round((self.safe_moves / self.moves) * 100, 1) if self.moves else 0.0

