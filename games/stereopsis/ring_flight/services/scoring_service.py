class RingFlightScoringService:
    SWITCH_STREAK = 3

    def __init__(self):
        self.reset()

    def reset(self):
        self.score = 0
        self.success_count = 0
        self.failure_count = 0
        self.current_streak = 0
        self.best_streak = 0
        self.wrong_depth_count = 0
        self.edge_hit_count = 0
        self.miss_count = 0
        self.target_switch_count = 0

    def on_success(self):
        self.success_count += 1
        self.current_streak += 1
        self.best_streak = max(self.best_streak, self.current_streak)
        gained = 18 + min(12, self.current_streak * 2)
        self.score += gained
        return gained

    def on_failure(self, reason):
        self.failure_count += 1
        self.current_streak = 0
        self.score = max(0, self.score - 6)
        if reason == "wrong_depth":
            self.wrong_depth_count += 1
        elif reason == "edge":
            self.edge_hit_count += 1
        elif reason == "miss":
            self.miss_count += 1

    def should_switch_target(self):
        return self.success_count > 0 and self.success_count % self.SWITCH_STREAK == 0

    def on_target_switch(self):
        self.target_switch_count += 1

    def accuracy(self):
        total = self.success_count + self.failure_count
        return round((self.success_count / total) * 100, 1) if total else 0.0
