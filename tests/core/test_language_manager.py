import unittest

from core.language_manager import LanguageManager


class LanguageManagerTests(unittest.TestCase):
    def setUp(self):
        LanguageManager._warned_missing_keys.clear()

    def test_missing_translation_key_warns_once_and_returns_key(self):
        manager = LanguageManager("zh-CN")
        with self.assertLogs("core.language_manager", level="WARNING") as logs:
            first = manager.t("missing.example.key")
            second = manager.t("missing.example.key")
        self.assertEqual(first, "missing.example.key")
        self.assertEqual(second, "missing.example.key")
        self.assertEqual(len(logs.output), 1)
        self.assertIn("missing.example.key", logs.output[0])


if __name__ == "__main__":
    unittest.main()
