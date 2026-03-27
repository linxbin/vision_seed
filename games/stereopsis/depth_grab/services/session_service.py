import time


class DepthGrabSessionService:
    def __init__(self, session_seconds):
        self.session_seconds = session_seconds
        self.reset()

    def reset(self):
        self.session_started_at = 0.0
        self.round_started_at = 0.0
        self.session_elapsed = 0.0
        self.round_elapsed = 0.0

    def start(self):
        now = time.time()
        self.session_started_at = now
        self.round_started_at = now
        self.session_elapsed = 0.0
        self.round_elapsed = 0.0

    def restart_round(self, now=None):
        self.round_started_at = now if now is not None else time.time()
        self.round_elapsed = 0.0

    def tick(self, now=None):
        now = now if now is not None else time.time()
        if self.session_started_at:
            self.session_elapsed = now - self.session_started_at
        if self.round_started_at:
            self.round_elapsed = now - self.round_started_at
        return self.session_elapsed, self.round_elapsed

    def is_complete(self):
        return self.session_started_at and self.session_elapsed >= self.session_seconds
