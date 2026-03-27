class PopNearestScoringService:
    def __init__(self):
        self.reset()

    def reset(self):
        self.score = 0
        self.correct_pops = 0
        self.wrong_pops = 0
        self.groups_cleared = 0
        self.best_streak = 0
        self.current_streak = 0
        self.total_pop_time = 0.0

    def on_correct(self, reaction_time):
        self.correct_pops += 1
        self.current_streak += 1
        self.best_streak = max(self.best_streak, self.current_streak)
        self.total_pop_time += reaction_time
        self.score += 14 + min(8, int(max(0.0, 2.4 - reaction_time) * 4))

    def on_wrong(self):
        self.wrong_pops += 1
        self.current_streak = 0

    def on_group_cleared(self):
        self.groups_cleared += 1
        self.score += 10

    def accuracy(self):
        total = self.correct_pops + self.wrong_pops
        return round((self.correct_pops / total) * 100, 1) if total else 0.0

    def average_pop_time(self):
        return round(self.total_pop_time / self.correct_pops, 2) if self.correct_pops else 0.0
