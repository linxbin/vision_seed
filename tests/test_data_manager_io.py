import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from core.data_manager import DataManager


class DataManagerIOTests(unittest.TestCase):
    def test_save_and_read_session_with_schema_version(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            with patch("core.data_manager.get_user_data_dir", return_value=tmp_dir), patch(
                "core.data_manager.get_install_root", return_value=tmp_dir
            ):
                manager = DataManager()

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
                self.assertIn("game_id", sessions[0])
                self.assertEqual(sessions[0]["game_id"], "legacy_training")
                self.assertEqual(sessions[0]["accuracy_rate"], 70.0)

    def test_atomic_write_replace_failure_keeps_original_file(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            with patch("core.data_manager.get_user_data_dir", return_value=tmp_dir), patch(
                "core.data_manager.get_install_root", return_value=tmp_dir
            ):
                manager = DataManager()

                baseline = manager._read_json()
                next_data = {"schema_version": DataManager.CURRENT_SCHEMA_VERSION, "sessions": [{"timestamp": "x"}]}

                with patch("core.data_manager.os.replace", side_effect=OSError("replace failed")):
                    manager._write_json(next_data)

                after = manager._read_json()
                self.assertEqual(after, baseline)

                tmp_files = list(Path(tmp_dir).glob(".records.*.tmp"))
                self.assertEqual(tmp_files, [])


if __name__ == "__main__":
    unittest.main()
