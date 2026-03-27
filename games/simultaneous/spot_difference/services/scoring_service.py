class SpotDifferenceScoringService:
    BASE_SCORE = 10
    COMBO_BONUS = 20
    COMBO_TRIGGER = 3

    def __init__(self):
        self.reset()

    def reset(self):
        self.score = 0
        self.success_count = 0
        self.combo = 0
        self.best_combo = 0
        self.reaction_times = []

    def on_success(self, reaction_time=None):
        self.success_count += 1
        self.combo += 1
        self.best_combo = max(self.best_combo, self.combo)
        if reaction_time is not None:
            self.reaction_times.append(max(0.0, float(reaction_time)))
        gained = self.BASE_SCORE
        if self.combo % self.COMBO_TRIGGER == 0:
            gained += self.COMBO_BONUS
        self.score += gained
        return gained

    def on_failure(self):
        self.combo = 0

    def average_reaction_time(self):
        if not self.reaction_times:
            return 0.0
        return round(sum(self.reaction_times) / len(self.reaction_times), 2)

