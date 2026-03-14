from dataclasses import dataclass


@dataclass
class ScoreState:
    attempt_count: int = 0
    correct_count: int = 0
    wrong_count: int = 0
    score: int = 0

    def reset(self):
        self.attempt_count = 0
        self.correct_count = 0
        self.wrong_count = 0
        self.score = 0

    def apply(self, success: bool, points: int):
        if success:
            self.correct_count += 1
            self.score += int(points)
        else:
            self.wrong_count += 1
        self.attempt_count += 1

    def accuracy_rate(self):
        total = self.correct_count + self.wrong_count
        return round((self.correct_count / total) * 100, 1) if total else 0.0
