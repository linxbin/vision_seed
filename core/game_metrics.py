def format_metric_value(value):
    if isinstance(value, bool):
        return "Yes" if value else "No"
    if isinstance(value, float):
        return f"{value:.1f}"
    return str(value)


METRIC_LABEL_KEYS = {
    "clear_window_hits": "catch_fruit.metric.label",
    "smallest_caught_size_px": "catch_fruit.metric.smallest",
    "binocular_merge_accuracy": "spot_difference.metric.label",
    "weak_eye_usage_rate": "weak_eye_key.metric.label",
    "depth_accuracy": "depth_grab.metric.label",
    "average_click_deviation_px": "precision_aim.metric.label",
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
