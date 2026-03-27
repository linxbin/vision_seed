class WhackAMoleScoringService:
    def __init__(self):
        self.reset()

    def reset(self):
        self.score = 0
        self.success_count = 0
        self.failure_count = 0
        self.center_hit_count = 0
        self.best_streak = 0
        self.current_streak = 0
        self.total_aim_time = 0.0

    def on_hit(self, distance, radius, reaction_time):
        if distance <= radius * 0.45:
            self.success_count += 1
            self.center_hit_count += 1
            self.current_streak += 1
            self.best_streak = max(self.best_streak, self.current_streak)
            self.score += 18
            self.total_aim_time += reaction_time
            return "center", 18
        if distance <= radius:
            self.success_count += 1
            self.current_streak += 1
            self.best_streak = max(self.best_streak, self.current_streak)
            self.score += 12
            self.total_aim_time += reaction_time
            return "good", 12
        self.failure_count += 1
        self.current_streak = 0
        return "miss", 0

    def on_timeout(self):
        self.failure_count += 1
        self.current_streak = 0

    def accuracy(self):
        total = self.success_count + self.failure_count
        return round((self.success_count / total) * 100, 1) if total else 0.0

    def center_hit_rate(self):
        return round((self.center_hit_count / self.success_count) * 100, 1) if self.success_count else 0.0

    def average_aim_time(self):
        return round(self.total_aim_time / self.success_count, 2) if self.success_count else 0.0

