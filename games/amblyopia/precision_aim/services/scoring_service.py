class PrecisionAimScoringService:
    def __init__(self):
        self.reset()

    def reset(self):
        self.score = 0
        self.success_count = 0
        self.failure_count = 0
        self.center_hit_count = 0
        self.best_center_streak = 0
        self.center_streak = 0
        self.deviations = []
        self.total_aim_time = 0.0
        self.smallest_target_hit = 0
        self.last_quality = "miss"
        self.stage_reached = 0

    def on_shot(self, distance, radius, reaction_time, stage_index):
        self.deviations.append(round(distance, 1))
        self.stage_reached = max(self.stage_reached, stage_index)
        if distance <= radius * 0.35:
            self.last_quality = "center"
            self.success_count += 1
            self.center_hit_count += 1
            self.center_streak += 1
            self.best_center_streak = max(self.best_center_streak, self.center_streak)
            self.total_aim_time += reaction_time
            self.smallest_target_hit = radius if self.smallest_target_hit == 0 else min(self.smallest_target_hit, radius)
            gained = 18 + (6 if self.center_streak >= 2 else 0)
            self.score += gained
            return True, gained
        if distance <= radius * 0.68:
            self.last_quality = "good"
            self.success_count += 1
            self.center_streak = 0
            self.total_aim_time += reaction_time
            self.smallest_target_hit = radius if self.smallest_target_hit == 0 else min(self.smallest_target_hit, radius)
            self.score += 12
            return True, 12
        if distance <= radius:
            self.last_quality = "edge"
            self.success_count += 1
            self.center_streak = 0
            self.total_aim_time += reaction_time
            self.smallest_target_hit = radius if self.smallest_target_hit == 0 else min(self.smallest_target_hit, radius)
            self.score += 8
            return True, 8
        self.last_quality = "miss"
        self.failure_count += 1
        self.center_streak = 0
        return False, 0

    def accuracy(self):
        total = self.success_count + self.failure_count
        return round((self.success_count / total) * 100, 1) if total else 0.0

    def average_deviation(self):
        return round(sum(self.deviations) / len(self.deviations), 1) if self.deviations else 0.0

    def average_aim_time(self):
        return round(self.total_aim_time / self.success_count, 2) if self.success_count else 0.0

    def center_hit_rate(self):
        if self.success_count == 0:
            return 0.0
        return round((self.center_hit_count / self.success_count) * 100, 1)
