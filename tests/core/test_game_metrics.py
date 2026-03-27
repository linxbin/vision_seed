import unittest

from core.game_metrics import summarize_session


class _ManagerStub:
    def t(self, key, **kwargs):
        if key == "catch_fruit.metric.label":
            return "Clear-window catches"
        if key == "fusion_push_box.metric.label":
            return "Fusion clear count"
        if key == "weak_eye_key.metric.accuracy":
            return "Weak-eye accuracy"
        if key == "precision_aim.metric.accuracy":
            return "Hit accuracy"
        if key == "precision_aim.metric.label":
            return "Average click deviation"
        if key == "depth_grab.metric.confusion":
            return "Front/back confusions"
        if key == "pop_nearest.metric.label":
            return "Depth order accuracy"
        if key == "pop_nearest.metric.avg_pop_time":
            return "Average pop time"
        if key == "pop_nearest.metric.groups":
            return "Groups cleared"
        if key == "snake_focus.metric.label":
            return "Best length"
        if key == "snake_focus.metric.foods":
            return "Foods eaten"
        if key == "red_blue_catch.metric.accuracy":
            return "Color match accuracy"
        if key == "metric.catch_accuracy":
            return "Catch accuracy"
        if key == "metric.best_length":
            return "Best length"
        if key == "metric.correct_pops":
            return "Correct pops"
        if key == "fusion_tetris.metric.lines":
            return "Lines Cleared"
        if key == "path_fusion.metric.accuracy":
            return "Fusion path accuracy"
        if key == "fruit_slice.metric.accuracy":
            return "Slice accuracy"
        if key == "metric.wrong_pops":
            return "Wrong pops"
        if key == "category.latest_summary":
            return f"Latest: {kwargs['accuracy']}% / {kwargs['duration']}s"
        if key == "category.latest_metric":
            return f"{kwargs['label']}: {kwargs['value']}"
        return key


class GameMetricsTests(unittest.TestCase):
    def test_summarize_session_with_metric(self):
        manager = _ManagerStub()
        line1, line2 = summarize_session(manager, {
            "accuracy_rate": 87.5,
            "duration_seconds": 45.2,
            "training_metrics": {"clear_window_hits": 6},
        })
        self.assertEqual(line1, "Latest: 87.5% / 45.2s")
        self.assertEqual(line2, "Clear-window catches: 6")

    def test_summarize_session_without_metric(self):
        manager = _ManagerStub()
        line1, line2 = summarize_session(manager, {"accuracy_rate": 50.0, "duration_seconds": 20.0})
        self.assertEqual(line1, "Latest: 50.0% / 20.0s")
        self.assertEqual(line2, "")

    def test_summarize_session_uses_fusion_metric_label(self):
        manager = _ManagerStub()
        _line1, line2 = summarize_session(manager, {
            "accuracy_rate": 90.0,
            "duration_seconds": 30.0,
            "training_metrics": {"fusion_clear_count": 3},
        })
        self.assertEqual(line2, "Fusion clear count: 3")

    def test_summarize_session_uses_weak_eye_metric_label(self):
        manager = _ManagerStub()
        _line1, line2 = summarize_session(manager, {
            "accuracy_rate": 78.0,
            "duration_seconds": 28.0,
            "training_metrics": {"weak_eye_accuracy": 78.0},
        })
        self.assertEqual(line2, "Weak-eye accuracy: 78.0")

    def test_summarize_session_uses_precision_aim_accuracy_label(self):
        manager = _ManagerStub()
        _line1, line2 = summarize_session(manager, {
            "accuracy_rate": 82.0,
            "duration_seconds": 33.0,
            "training_metrics": {"hit_accuracy": 82.0},
        })
        self.assertEqual(line2, "Hit accuracy: 82.0")

    def test_summarize_session_uses_new_batch_metric_label(self):
        manager = _ManagerStub()
        _line1, line2 = summarize_session(manager, {
            "accuracy_rate": 88.0,
            "duration_seconds": 31.0,
            "training_metrics": {"lines_cleared": 4},
        })
        self.assertEqual(line2, "Lines Cleared: 4")

    def test_summarize_session_uses_color_match_metric_label(self):
        manager = _ManagerStub()
        _line1, line2 = summarize_session(manager, {
            "accuracy_rate": 76.0,
            "duration_seconds": 29.0,
            "training_metrics": {"color_match_accuracy": 76.0},
        })
        self.assertEqual(line2, "Color match accuracy: 76.0")

    def test_summarize_session_uses_red_blue_catch_saved_metric_label(self):
        manager = _ManagerStub()
        _line1, line2 = summarize_session(manager, {
            "accuracy_rate": 76.0,
            "duration_seconds": 29.0,
            "training_metrics": {"catch_accuracy": 76.0},
        })
        self.assertEqual(line2, "Catch accuracy: 76.0")

    def test_summarize_session_uses_snake_saved_metric_label(self):
        manager = _ManagerStub()
        _line1, line2 = summarize_session(manager, {
            "accuracy_rate": 84.0,
            "duration_seconds": 21.0,
            "training_metrics": {"best_length": 9},
        })
        self.assertEqual(line2, "Best length: 9")

    def test_summarize_session_uses_pop_nearest_metric_label(self):
        manager = _ManagerStub()
        _line1, line2 = summarize_session(manager, {
            "accuracy_rate": 89.0,
            "duration_seconds": 24.0,
            "training_metrics": {"depth_order_accuracy": 89.0},
        })
        self.assertEqual(line2, "Depth order accuracy: 89.0")


if __name__ == "__main__":
    unittest.main()
