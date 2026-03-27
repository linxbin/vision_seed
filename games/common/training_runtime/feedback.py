from dataclasses import dataclass
import time


@dataclass
class FeedbackState:
    text: str = ""
    color: tuple[int, int, int] = (255, 255, 255)
    until: float = 0.0

    def set(self, text: str, color: tuple[int, int, int], duration: float = 1.0, now: float | None = None):
        current = time.time() if now is None else float(now)
        self.text = text
        self.color = color
        self.until = current + duration

    def clear_if_expired(self, now: float | None = None):
        current = time.time() if now is None else float(now)
        if self.text and current > self.until:
            self.text = ""

