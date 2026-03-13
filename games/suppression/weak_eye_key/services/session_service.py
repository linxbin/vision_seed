import time


class WeakEyeKeySessionService:
    def __init__(self, session_seconds, round_seconds=18):
        self.session_seconds = session_seconds
        self.round_seconds = round_seconds
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
        self.round_started_at = time.time() if now is None else now
        self.round_elapsed = 0.0

    def tick(self, now=None):
        now = time.time() if now is None else now
        if self.session_started_at <= 0.0:
            return 0.0, 0.0
        self.session_elapsed = max(0.0, now - self.session_started_at)
        self.round_elapsed = max(0.0, now - self.round_started_at)
        return self.session_elapsed, self.round_elapsed

    def is_complete(self):
        return self.session_elapsed >= self.session_seconds

    def is_round_timeout(self):
        return self.round_elapsed >= self.round_seconds
