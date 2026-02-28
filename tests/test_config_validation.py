import tempfile
import unittest
from pathlib import Path

from core.preferences_manager import PreferencesManager


class ConfigValidationTests(unittest.TestCase):
    def test_preferences_sanitize_bounds_and_language(self):
        manager = PreferencesManager()
        with tempfile.TemporaryDirectory() as tmp_dir:
            manager.preferences_file = str(Path(tmp_dir) / "user_preferences.json")

            raw = {
                "start_level": 999,
                "total_questions": -5,
                "sound_enabled": 1,
                "language": "invalid-lang",
            }
            self.assertTrue(manager.save_preferences(raw))
            loaded = manager.load_preferences()

            self.assertEqual(loaded["start_level"], 10)
            self.assertEqual(loaded["total_questions"], 0)
            self.assertTrue(loaded["sound_enabled"])
            self.assertEqual(loaded["language"], "en-US")


if __name__ == "__main__":
    unittest.main()
