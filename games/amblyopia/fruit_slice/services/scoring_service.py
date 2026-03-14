class FruitSliceScoringService:
    def __init__(self):
        self.reset()

    def reset(self):
        self.score = 0
        self.success_count = 0
        self.failure_count = 0
        self.combo = 0
        self.best_combo = 0

    def on_target(self):
        self.success_count += 1
        self.combo += 1
        self.best_combo = max(self.best_combo, self.combo)
        self.score += 12 + (4 if self.combo >= 3 else 0)

    def on_failure(self):
        self.failure_count += 1
        self.combo = 0

    def accuracy(self):
        total = self.success_count + self.failure_count
        return round((self.success_count / total) * 100, 1) if total else 0.0

