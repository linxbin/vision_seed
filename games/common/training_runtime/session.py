from dataclasses import dataclass
import time


@dataclass
class SessionState:
    session_started_at: float = 0.0
    round_started_at: float = 0.0
    session_elapsed: float = 0.0
    round_elapsed: float = 0.0

    def reset(self):
        self.session_started_at = 0.0
        self.round_started_at = 0.0
        self.session_elapsed = 0.0
        self.round_elapsed = 0.0

    def start_session(self, now: float | None = None):
        current = time.time() if now is None else float(now)
        self.session_started_at = current
        self.round_started_at = current
        self.session_elapsed = 0.0
        self.round_elapsed = 0.0

    def start_round(self, now: float | None = None):
        current = time.time() if now is None else float(now)
        self.round_started_at = current
        self.round_elapsed = 0.0

    def tick(self, now: float | None = None):
        current = time.time() if now is None else float(now)
        if self.session_started_at > 0:
            self.session_elapsed = current - self.session_started_at
        if self.round_started_at > 0:
            self.round_elapsed = current - self.round_started_at

