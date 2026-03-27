import time


class SpotDifferenceSessionService:
    def __init__(self, session_seconds):
        self.session_seconds = session_seconds
        self.reset()

    def reset(self):
        self.session_started_at = 0.0
        self.session_elapsed = 0.0

    def start(self, now=None):
        current = time.time() if now is None else float(now)
        self.session_started_at = current
        self.session_elapsed = 0.0

    def tick(self, now=None):
        current = time.time() if now is None else float(now)
        if self.session_started_at > 0:
            self.session_elapsed = current - self.session_started_at
        return self.session_elapsed

    def is_complete(self):
        return self.session_elapsed >= self.session_seconds

