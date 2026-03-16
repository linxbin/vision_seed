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
                        "training_metrics": {"clear_window_hits": 4},
                    }
                )
                self.assertTrue(ok)
                sessions = manager.get_all_sessions()
                self.assertEqual(len(sessions), 1)
                self.assertEqual(sessions[0]["schema_version"], DataManager.CURRENT_SCHEMA_VERSION)
                self.assertEqual(sessions[0]["game_id"], "legacy_training")
                self.assertEqual(sessions[0]["accuracy_rate"], 70.0)
                self.assertEqual(sessions[0]["training_metrics"]["clear_window_hits"], 4)

    def test_atomic_write_replace_failure_keeps_original_file(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            with patch("core.data_manager.get_user_data_dir", return_value=tmp_dir), patch(
                "core.data_manager.get_install_root", return_value=tmp_dir
            ):
                manager = DataManager()
                baseline = manager._read_json()
                next_data = {"schema_version": DataManager.CURRENT_SCHEMA_VERSION, "sessions": [{"timestamp": "x"}]}
                with self.assertLogs("core.data_manager", level="WARNING") as logs:
                    with patch("core.data_manager.os.replace", side_effect=OSError("replace failed")):
                        manager._write_json(next_data)
                self.assertTrue(any("Error writing records file: replace failed" in line for line in logs.output))
                after = manager._read_json()
                self.assertEqual(after, baseline)
                self.assertEqual(list(Path(tmp_dir).glob(".records.*.tmp")), [])

    def test_save_training_session_returns_false_when_write_fails(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            with patch("core.data_manager.get_user_data_dir", return_value=tmp_dir), patch(
                "core.data_manager.get_install_root", return_value=tmp_dir
            ):
                manager = DataManager()
                with self.assertLogs("core.data_manager", level="WARNING") as logs:
                    with patch("core.data_manager.os.replace", side_effect=OSError("replace failed")):
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
                self.assertFalse(ok)
                self.assertTrue(any("Error writing records file: replace failed" in line for line in logs.output))

    def test_get_sessions_by_game_filters_namespace(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            with patch("core.data_manager.get_user_data_dir", return_value=tmp_dir), patch(
                "core.data_manager.get_install_root", return_value=tmp_dir
            ):
                manager = DataManager()
                manager.save_training_session({
                    "timestamp": "2026-02-27T00:00:00",
                    "game_id": "accommodation.e_orientation",
                    "difficulty_level": 3,
                    "total_questions": 10,
                    "correct_count": 7,
                    "wrong_count": 3,
                    "duration_seconds": 12.3,
                })
                manager.save_training_session({
                    "timestamp": "2026-02-27T01:00:00",
                    "game_id": "simultaneous.eye_find_patterns",
                    "difficulty_level": 2,
                    "total_questions": 8,
                    "correct_count": 6,
                    "wrong_count": 2,
                    "duration_seconds": 20.0,
                    "training_metrics": {"depth_accuracy": 80.0},
                })
                e_sessions = manager.get_sessions_by_game("accommodation.e_orientation")
                eye_sessions = manager.get_sessions_by_game("simultaneous.eye_find_patterns")
                self.assertEqual(len(e_sessions), 1)
                self.assertEqual(len(eye_sessions), 1)
                self.assertEqual(e_sessions[0]["game_id"], "accommodation.e_orientation")
                self.assertEqual(manager.get_latest_session("simultaneous.eye_find_patterns")["game_id"], "simultaneous.eye_find_patterns")
                self.assertEqual(eye_sessions[0]["training_metrics"]["depth_accuracy"], 80.0)


if __name__ == "__main__":
    unittest.main()
