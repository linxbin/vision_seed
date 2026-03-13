class WeakEyeKeyScoringService:
    def __init__(self):
        self.reset()

    def reset(self):
        self.score = 0
        self.success_count = 0
        self.failure_count = 0
        self.current_streak = 0
        self.best_streak = 0
        self.total_find_time = 0.0
        self.stage_reached = 0

    def on_success(self, find_time, stage_index):
        self.success_count += 1
        self.current_streak += 1
        self.best_streak = max(self.best_streak, self.current_streak)
        self.total_find_time += max(0.0, float(find_time))
        self.stage_reached = max(self.stage_reached, stage_index)
        gained = 24 + stage_index * 6 + min(12, self.current_streak * 2)
        self.score += gained
        return gained

    def on_failure(self):
        self.failure_count += 1
        self.current_streak = 0

    def average_find_time(self):
        if self.success_count <= 0:
            return 0.0
        return round(self.total_find_time / self.success_count, 2)
