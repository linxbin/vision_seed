class SnakeScoringService:
    def __init__(self):
        self.reset()

    def reset(self):
        self.score = 0
        self.food_count = 0
        self.collision_count = 0
        self.best_length = 3
        self.safe_steps = 0
        self.total_steps = 0

    def on_step(self, length):
        self.safe_steps += 1
        self.total_steps += 1
        self.best_length = max(self.best_length, length)

    def on_food(self, length):
        self.food_count += 1
        self.score += 15
        self.best_length = max(self.best_length, length)

    def on_collision(self):
        self.collision_count += 1
        self.total_steps += 1

    def accuracy(self):
        return round((self.safe_steps / self.total_steps) * 100, 1) if self.total_steps else 0.0

