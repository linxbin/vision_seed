class BrickBreakerScoringService:
    def __init__(self):
        self.reset()

    def reset(self):
        self.score = 0
        self.brick_count = 0
        self.miss_count = 0
        self.shot_count = 0
        self.depth_confusion = 0
        self.target_hits = 0
        self.wrong_layer_hits = 0
        self.refresh_count = 0

    def on_launch(self):
        self.shot_count += 1

    def on_hit(self, matched_depth):
        if matched_depth:
            self.brick_count += 1
            self.target_hits += 1
            self.score += 20
            return True
        self.depth_confusion += 1
        self.wrong_layer_hits += 1
        self.score = max(0, self.score - 5)
        return False

    def on_miss(self):
        self.miss_count += 1

    def on_refresh(self):
        self.refresh_count += 1

    def accuracy(self):
        total = self.target_hits + self.wrong_layer_hits + self.miss_count
        return round((self.target_hits / total) * 100, 1) if total else 0.0
