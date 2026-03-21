def format_metric_value(value):
    if isinstance(value, bool):
        return "Yes" if value else "No"
    if isinstance(value, float):
        return f"{value:.1f}"
    return str(value)


METRIC_LABEL_KEYS = {
    "clear_window_hits": "catch_fruit.metric.label",
    "smallest_caught_size_px": "catch_fruit.metric.smallest",
    "best_length": "metric.best_length",
    "catch_accuracy": "metric.catch_accuracy",
    "miss_count": "metric.miss_count",
    "best_combo": "metric.best_combo",
    "best_streak": "metric.best_streak",
    "bonus_hits": "metric.bonus_hits",
    "fusion_clear_count": "fusion_push_box.metric.label",
    "total_steps": "metric.total_steps",
    "total_pushes": "metric.total_pushes",
    "avg_solve_time": "metric.avg_solve_time",
    "binocular_merge_accuracy": "spot_difference.metric.label",
    "avg_find_time": "metric.avg_find_time",
    "pong_best_rally": "pong.metric.label",
    "player_hits": "metric.player_hits",
    "return_accuracy": "metric.return_accuracy",
    "weak_eye_accuracy": "weak_eye_key.metric.accuracy",
    "weak_eye_usage_rate": "weak_eye_key.metric.label",
    "clue_match_accuracy": "weak_eye_key.metric.label",
    "depth_accuracy": "depth_grab.metric.label",
    "front_back_confusion_count": "depth_grab.metric.confusion",
    "avg_grab_time": "metric.avg_grab_time",
    "stage_reached": "metric.stage_reached",
    "hit_accuracy": "precision_aim.metric.accuracy",
    "center_hit_rate": "precision_aim.metric.center_rate",
    "average_click_deviation_px": "precision_aim.metric.label",
    "avg_aim_time": "metric.avg_aim_time",
    "smallest_target_hit": "metric.smallest_target_hit",
    "best_center_streak": "metric.best_center_streak",
    "foods_eaten": "snake_focus.metric.foods",
    "color_match_accuracy": "red_blue_catch.metric.accuracy",
    "brick_clear_count": "brick_breaker.metric.cleared",
    "safe_crosses": "frogger.metric.crosses",
    "fall_count": "metric.fall_count",
    "successful_passes": "ring_flight.metric.label",
    "wrong_depth_count": "ring_flight.metric.wrong_depth",
    "edge_hit_count": "ring_flight.metric.edge_hit",
    "target_switch_count": "ring_flight.metric.switches",
    "lines_cleared": "fusion_tetris.metric.lines",
    "max_speed_level": "metric.max_speed_level",
    "fusion_accuracy": "metric.fusion_accuracy",
    "fusion_path_accuracy": "path_fusion.metric.accuracy",
    "slice_accuracy": "fruit_slice.metric.accuracy",
}


def summarize_session(manager, session):
    if not isinstance(session, dict) or not session:
        return "", ""
    accuracy = float(session.get("accuracy_rate", 0.0))
    duration = float(session.get("duration_seconds", 0.0))
    line1 = manager.t("category.latest_summary", accuracy=f"{accuracy:.1f}", duration=f"{duration:.1f}")
    metrics = session.get("training_metrics", {})
    if not isinstance(metrics, dict) or not metrics:
        return line1, ""
    key, value = next(iter(metrics.items()))
    label_key = METRIC_LABEL_KEYS.get(key, "")
    label = manager.t(label_key) if label_key else key
    line2 = manager.t("category.latest_metric", label=label, value=format_metric_value(value))
    return line1, line2
