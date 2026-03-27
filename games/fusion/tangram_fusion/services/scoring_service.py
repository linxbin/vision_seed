class TangramFusionScoringService:
    def __init__(self):
        self.reset()

    def reset(self):
        self.score = 0
        self.success_count = 0
        self.failure_count = 0
        self.completed_shapes = 0
        self.current_streak = 0
        self.best_streak = 0
        self.total_select_time = 0.0

    def on_answer(self, correct, response_time, stage_index):
        response_time = max(0.0, float(response_time))
        self.total_select_time += response_time
        if correct:
            self.success_count += 1
            self.completed_shapes += 1
            self.current_streak += 1
            self.best_streak = max(self.best_streak, self.current_streak)
            stage_bonus = (10, 14, 18)[stage_index]
            speed_bonus = 6 if response_time <= 1.8 else 3 if response_time <= 3.0 else 0
            self.score += stage_bonus + speed_bonus
            return True
        self.failure_count += 1
        self.current_streak = 0
        return False

    def accuracy(self):
        total = self.success_count + self.failure_count
        return round((self.success_count / total) * 100, 1) if total else 0.0

    def average_select_time(self):
        total = self.success_count + self.failure_count
        return round(self.total_select_time / total, 2) if total else 0.0
