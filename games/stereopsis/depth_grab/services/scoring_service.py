class DepthGrabScoringService:
    def __init__(self):
        self.reset()

    def reset(self):
        self.score = 0
        self.success_count = 0
        self.failure_count = 0
        self.best_streak = 0
        self.current_streak = 0
        self.total_reaction_time = 0.0
        self.front_back_confusion_count = 0
        self.stage_reached = 0

    def on_success(self, reaction_time, stage_index):
        self.success_count += 1
        self.current_streak += 1
        self.best_streak = max(self.best_streak, self.current_streak)
        self.total_reaction_time += reaction_time
        self.stage_reached = max(self.stage_reached, stage_index)
        gained = 16 + stage_index * 4 + min(8, int(max(0.0, 5.0 - reaction_time) * 2))
        if self.current_streak >= 3:
            gained += 6
        self.score += gained
        return gained

    def on_failure(self, selected_depth_rank):
        self.failure_count += 1
        if selected_depth_rank is not None and selected_depth_rank != 0:
            self.front_back_confusion_count += 1
        self.current_streak = 0

    def accuracy(self):
        total = self.success_count + self.failure_count
        return round((self.success_count / total) * 100, 1) if total else 0.0

    def average_reaction_time(self):
        return round(self.total_reaction_time / self.success_count, 2) if self.success_count else 0.0

