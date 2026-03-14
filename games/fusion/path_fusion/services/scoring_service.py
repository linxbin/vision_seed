class PathFusionScoringService:
    def __init__(self):
        self.reset()

    def reset(self):
        self.score = 0
        self.success_count = 0
        self.failure_count = 0

    def on_answer(self, correct):
        if correct:
            self.success_count += 1
            self.score += 14
            return True
        self.failure_count += 1
        return False

    def accuracy(self):
        total = self.success_count + self.failure_count
        return round((self.success_count / total) * 100, 1) if total else 0.0

