import time


class PathFusionSessionService:
    def __init__(self, session_seconds):
        self.session_seconds = session_seconds
        self.reset()

    def reset(self):
        self.session_started_at = 0.0
        self.session_elapsed = 0.0

    def start(self):
        self.session_started_at = time.time()
        self.session_elapsed = 0.0

    def tick(self, now=None):
        now = time.time() if now is None else now
        if self.session_started_at:
            self.session_elapsed = now - self.session_started_at
        return self.session_elapsed

    def is_complete(self):
        return self.session_started_at and self.session_elapsed >= self.session_seconds
