class EyeFindScoringService:
    BASE_SCORE = 10
    COMBO_BONUS_SCORE = 20
    COMBO_TRIGGER = 3

    def __init__(self):
        self.score = 0
        self.success_count = 0
        self.combo = 0

    def reset(self):
        self.score = 0
        self.success_count = 0
        self.combo = 0

    def on_success(self):
        self.success_count += 1
        self.combo += 1
        gained = self.BASE_SCORE
        if self.combo % self.COMBO_TRIGGER == 0:
            gained += self.COMBO_BONUS_SCORE
        self.score += gained
        return gained

    def on_failure(self):
        self.combo = 0
