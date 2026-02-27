import tempfile
import unittest
from pathlib import Path

from core.data_manager import DataManager


class DataManagerIOTests(unittest.TestCase):
    def test_save_and_read_session_with_schema_version(self):
        manager = DataManager()
        with tempfile.TemporaryDirectory() as tmp_dir:
            manager.records_file = str(Path(tmp_dir) / "records.json")
            manager._init_records_file()

            ok = manager.save_training_session(
                {
                    "timestamp": "2026-02-27T00:00:00",
                    "difficulty_level": 3,
                    "total_questions": 10,
                    "correct_count": 7,
                    "wrong_count": 3,
                    "duration_seconds": 12.3,
                }
            )
            self.assertTrue(ok)

            sessions = manager.get_all_sessions()
            self.assertEqual(len(sessions), 1)
            self.assertEqual(sessions[0]["schema_version"], DataManager.CURRENT_SCHEMA_VERSION)
            self.assertIn("e_size_px", sessions[0])
            self.assertIn("session_id", sessions[0])
            self.assertEqual(sessions[0]["accuracy_rate"], 70.0)


if __name__ == "__main__":
    unittest.main()
