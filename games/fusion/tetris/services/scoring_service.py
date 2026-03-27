class FusionTetrisScoringService:
    def __init__(self):
        self.reset()

    def reset(self):
        self.score = 0
        self.lines_cleared = 0
        self.failures = 0
        self.moves = 0
        self.correct_moves = 0

    def on_line(self, count=1):
        self.lines_cleared += count
        self.score += 20 * count
        self.moves += 1
        self.correct_moves += 1

    def on_safe_drop(self):
        self.moves += 1
        self.correct_moves += 1
        self.score += 4

    def on_failure(self):
        self.moves += 1
        self.failures += 1

    def accuracy(self):
        return round((self.correct_moves / self.moves) * 100, 1) if self.moves else 0.0

