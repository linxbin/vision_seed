import time


class EyeFindSessionService:
    def __init__(self, session_seconds, attempt_seconds):
        self.session_seconds = session_seconds
        self.attempt_seconds = attempt_seconds
        self.session_started_at = 0.0
        self.attempt_started_at = 0.0
        self.session_elapsed = 0.0
        self.attempt_elapsed = 0.0

    def reset(self):
        self.session_started_at = 0.0
        self.attempt_started_at = 0.0
        self.session_elapsed = 0.0
        self.attempt_elapsed = 0.0

    def start(self, now=None):
        current = time.time() if now is None else float(now)
        self.session_started_at = current
        self.attempt_started_at = current
        self.session_elapsed = 0.0
        self.attempt_elapsed = 0.0

    def restart_attempt(self, now=None):
        current = time.time() if now is None else float(now)
        self.attempt_started_at = current
        self.attempt_elapsed = 0.0

    def tick(self, now=None):
        current = time.time() if now is None else float(now)
        if self.session_started_at > 0:
            self.session_elapsed = current - self.session_started_at
        if self.attempt_started_at > 0:
            self.attempt_elapsed = current - self.attempt_started_at
        return self.session_elapsed, self.attempt_elapsed

    def is_session_complete(self):
        return self.session_elapsed >= self.session_seconds

    def is_attempt_timed_out(self):
        return self.attempt_elapsed >= self.attempt_seconds

    def build_final_stats(self, scoring, mode, filter_direction):
        return {
            "duration": int(max(0.0, self.session_elapsed)),
            "success": int(scoring.success_count),
            "score": int(scoring.score),
            "mode": mode,
            "filter_direction": filter_direction,
        }
