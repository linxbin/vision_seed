from datetime import datetime
from unittest.mock import Mock


def _parse_timestamp(value):
    if not isinstance(value, str) or not value:
        return None
    try:
        dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
        if dt.tzinfo is not None:
            dt = dt.astimezone().replace(tzinfo=None)
        return dt
    except Exception:
        return None


def _is_same_day(dt, target):
    return bool(dt) and dt.date() == target.date()


def _safe_sequence(value):
    if value is None or isinstance(value, (str, bytes, Mock)):
        return []
    if isinstance(value, list):
        return value
    if isinstance(value, tuple):
        return list(value)
    try:
        return list(value)
    except TypeError:
        return []


def _safe_mapping(value):
    return value if isinstance(value, dict) else {}


def build_daily_plan(manager, limit=3):
    registry = getattr(manager, "game_registry", None)
    data_manager = getattr(manager, "data_manager", None)
    if not registry or not data_manager:
        return []

    now = datetime.now()
    plans = []
    categories = _safe_sequence(registry.get_categories()) if hasattr(registry, "get_categories") else []
    for category in categories:
        if not isinstance(category, dict) or not category.get("id"):
            continue
        games = _safe_sequence(registry.get_games_by_category(category["id"])) if hasattr(registry, "get_games_by_category") else []
        if not games:
            continue
        selected_game = None
        selected_latest = None
        best_score = None
        trained_today = False
        for game in games:
            if not getattr(game, "game_id", None):
                continue
            latest = _safe_mapping(data_manager.get_latest_session(game.game_id))
            latest_dt = _parse_timestamp(latest.get("timestamp", ""))
            accuracy = float(latest.get("accuracy_rate", 0.0))
            game_trained_today = _is_same_day(latest_dt, now)
            score = (1 if game_trained_today else 0, accuracy)
            if best_score is None or score < best_score:
                best_score = score
                selected_game = game
                selected_latest = latest
            trained_today = trained_today or game_trained_today
        if selected_game is None:
            continue
        accuracy = float(selected_latest.get("accuracy_rate", 0.0)) if selected_latest else 0.0
        reason_key = "menu.recommend.fresh" if not trained_today else "menu.recommend.review"
        plans.append({
            "category_id": category["id"],
            "category_name": manager.t(category.get("name_key") or category.get("name", "")),
            "game_id": selected_game.game_id,
            "game_name": manager.t(selected_game.name_key) if getattr(selected_game, "name_key", "") else selected_game.name,
            "reason_key": reason_key,
            "accuracy": accuracy,
            "trained_today": trained_today,
        })

    plans.sort(key=lambda item: (1 if item["trained_today"] else 0, item["accuracy"], item["category_name"]))
    return plans[:limit]


def build_daily_suggestion(manager, plans):
    if not plans:
        return manager.t("menu.recommend.none")
    fresh_count = sum(1 for item in plans if not item["trained_today"])
    if fresh_count >= 2:
        return manager.t("menu.recommend.start_fresh")
    lowest = min(plans, key=lambda item: item["accuracy"])
    return manager.t("menu.recommend.review_focus", category=lowest["category_name"])
