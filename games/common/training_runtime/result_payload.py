from datetime import datetime


def build_training_result_payload(*, game_id: str, difficulty_level: int, correct_count: int, wrong_count: int, duration_seconds: float, training_metrics: dict):
    return {
        "timestamp": datetime.now().replace(microsecond=0).isoformat(),
        "game_id": game_id,
        "difficulty_level": difficulty_level,
        "total_questions": correct_count + wrong_count,
        "correct_count": correct_count,
        "wrong_count": wrong_count,
        "duration_seconds": round(duration_seconds, 1),
        "training_metrics": training_metrics,
    }
