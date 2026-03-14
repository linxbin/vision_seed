class CatchFruitScoringService:
    def __init__(self):
        self.reset()

    def reset(self):
        self.score = 0
        self.success_count = 0
        self.failure_count = 0
        self.clear_hits = 0
        self.smallest_caught = 0
        self.current_streak = 0
        self.best_streak = 0
        self.bonus_hits = 0
        self.stage_reached = 0
        self.last_success_bonus = False

    def on_catch(self, current_size, clarity, fruit_name, stage_index, fruit_points):
        self.success_count += 1
        self.stage_reached = max(self.stage_reached, stage_index)
        self.smallest_caught = current_size if self.smallest_caught == 0 else min(self.smallest_caught, current_size)
        if clarity >= 0.75:
            self.clear_hits += 1
        self.current_streak += 1
        self.best_streak = max(self.best_streak, self.current_streak)
        self.last_success_bonus = fruit_name == "watermelon"
        if self.last_success_bonus:
            self.bonus_hits += 1
        gained = fruit_points.get(fruit_name, 10)
        if self.current_streak >= 3:
            gained += 8
        if self.last_success_bonus:
            gained += 12
        self.score += gained
        return gained

    def on_miss(self):
        self.failure_count += 1
        self.current_streak = 0
        self.last_success_bonus = False

    def accuracy(self):
        total = self.success_count + self.failure_count
        return round((self.success_count / total) * 100, 1) if total else 0.0

