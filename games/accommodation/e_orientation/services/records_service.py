class ETrainingRecordsService:
    GAME_ID = "accommodation.e_orientation"

    def __init__(self, data_manager):
        self.data_manager = data_manager

    def get_sessions(self):
        method = getattr(self.data_manager, "get_sessions_by_game", None)
        if callable(method):
            sessions = method(self.GAME_ID)
            if isinstance(sessions, list):
                return sessions

        fallback = getattr(self.data_manager, "get_all_sessions", None)
        sessions = fallback() if callable(fallback) else []
        if not isinstance(sessions, list):
            return []
        return [session for session in sessions if session.get("game_id", self.GAME_ID) == self.GAME_ID]

    def get_previous_session(self):
        sessions = self.get_sessions()
        return sessions[1] if len(sessions) > 1 else None

    def save_session(self, session_data):
        payload = dict(session_data)
        payload["game_id"] = self.GAME_ID
        return self.data_manager.save_training_session(payload)
