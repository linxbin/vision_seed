import unittest

from core.game_metrics import summarize_session


class _ManagerStub:
    def t(self, key, **kwargs):
        if key == "catch_fruit.metric.label":
            return "Clear-window catches"
        if key == "precision_aim.metric.label":
            return "Average click deviation"
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


if __name__ == "__main__":
    unittest.main()
