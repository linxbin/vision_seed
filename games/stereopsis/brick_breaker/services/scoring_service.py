class BrickBreakerScoringService:
    def __init__(self):
        self.reset()

    def reset(self):
        self.score = 0
        self.brick_count = 0
        self.miss_count = 0
        self.paddle_hits = 0
        self.depth_confusion = 0

    def on_brick(self, depth):
        self.brick_count += 1
        self.score += 12 + (2 - depth) * 4
        if depth > 0:
            self.depth_confusion += 1

    def on_paddle(self):
        self.paddle_hits += 1

    def on_miss(self):
        self.miss_count += 1

    def accuracy(self):
        total = self.paddle_hits + self.miss_count
        return round((self.paddle_hits / total) * 100, 1) if total else 0.0

