class FusionPushBoxScoringService:
    def __init__(self):
        self.reset()

    def reset(self):
        self.score = 0
        self.clear_count = 0
        self.best_streak = 0
        self.current_streak = 0
        self.total_steps = 0
        self.total_pushes = 0

    def register_step(self, pushed):
        self.total_steps += 1
        if pushed:
            self.total_pushes += 1

    def on_clear(self, steps, pushes):
        self.clear_count += 1
        self.current_streak += 1
        self.best_streak = max(self.best_streak, self.current_streak)
        efficiency_bonus = max(20, 120 - steps * 3)
        push_bonus = max(10, 40 - max(0, pushes - 1) * 5)
        gained = 80 + efficiency_bonus + push_bonus + (self.current_streak - 1) * 15
        self.score += gained
        return gained
