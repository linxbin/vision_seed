import time


class PopNearestSessionService:
    def __init__(self, session_seconds=300, group_seconds=12):
        self.session_seconds = session_seconds
        self.group_seconds = group_seconds
        self.reset()

    def reset(self):
        self.session_started_at = 0.0
        self.group_started_at = 0.0
        self.session_elapsed = 0.0
        self.group_elapsed = 0.0
        self.completed_groups = 0

    def start(self):
        now = time.time()
        self.session_started_at = now
        self.group_started_at = now
        self.session_elapsed = 0.0
        self.group_elapsed = 0.0
        self.completed_groups = 0

    def next_group(self, now=None):
        now = now if now is not None else time.time()
        self.completed_groups += 1
        self.group_started_at = now
        self.group_elapsed = 0.0

    def tick(self, now=None):
        now = now if now is not None else time.time()
        if self.session_started_at:
            self.session_elapsed = now - self.session_started_at
        if self.group_started_at:
            self.group_elapsed = now - self.group_started_at
        return self.session_elapsed, self.group_elapsed

    def session_time_left(self):
        return max(0.0, self.session_seconds - self.session_elapsed)

    def is_group_timeout(self):
        return self.group_started_at and self.group_elapsed >= self.group_seconds

    def is_complete(self):
        return self.session_started_at and self.session_elapsed >= self.session_seconds
