import unittest

from core.adaptive_manager import AdaptiveManager


class AdaptiveManagerTests(unittest.TestCase):
    def setUp(self):
        self.manager = AdaptiveManager()

    def _session(self, acc, duration, total=10):
        return {
            "accuracy_rate": acc,
            "duration_seconds": duration,
            "total_questions": total,
        }

    def test_upgrade_when_recent_three_are_fast_and_accurate(self):
        sessions = [
            self._session(90.0, 18.0, 10),
            self._session(88.0, 19.0, 10),
            self._session(86.0, 20.0, 10),
        ]
        result = self.manager.evaluate(
            sessions=sessions,
            current_level=5,
            min_level=1,
            max_level=10,
            enabled=True,
            cooldown_left=0,
        )
        self.assertEqual(result["reason_code"], "UP")
        self.assertEqual(result["new_level"], 4)
        self.assertTrue(result["changed"])
        self.assertEqual(result["cooldown_left"], 2)

    def test_downgrade_when_recent_three_are_low_accuracy(self):
        sessions = [
            self._session(58.0, 24.0, 10),
            self._session(62.0, 25.0, 10),
            self._session(60.0, 24.0, 10),
        ]
        result = self.manager.evaluate(
            sessions=sessions,
            current_level=5,
            min_level=1,
            max_level=10,
            enabled=True,
            cooldown_left=0,
        )
        self.assertEqual(result["reason_code"], "DOWN")
        self.assertEqual(result["new_level"], 6)
        self.assertTrue(result["changed"])
        self.assertEqual(result["cooldown_left"], 2)

    def test_keep_when_middle_band(self):
        sessions = [
            self._session(78.0, 24.0, 10),
            self._session(74.0, 23.0, 10),
            self._session(76.0, 22.0, 10),
        ]
        result = self.manager.evaluate(
            sessions=sessions,
            current_level=5,
            min_level=1,
            max_level=10,
            enabled=True,
            cooldown_left=0,
        )
        self.assertEqual(result["reason_code"], "KEEP")
        self.assertEqual(result["new_level"], 5)
        self.assertFalse(result["changed"])

    def test_respects_cooldown(self):
        sessions = [self._session(95.0, 15.0, 10)] * 3
        result = self.manager.evaluate(
            sessions=sessions,
            current_level=5,
            min_level=1,
            max_level=10,
            enabled=True,
            cooldown_left=2,
        )
        self.assertEqual(result["reason_code"], "COOLDOWN")
        self.assertEqual(result["new_level"], 5)
        self.assertEqual(result["cooldown_left"], 1)

    def test_insufficient_sessions(self):
        sessions = [self._session(95.0, 15.0, 10), self._session(92.0, 16.0, 10)]
        result = self.manager.evaluate(
            sessions=sessions,
            current_level=5,
            min_level=1,
            max_level=10,
            enabled=True,
            cooldown_left=0,
        )
        self.assertEqual(result["reason_code"], "INSUFFICIENT")
        self.assertEqual(result["new_level"], 5)
        self.assertFalse(result["changed"])


if __name__ == "__main__":
    unittest.main()
