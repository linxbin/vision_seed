import os
import unittest
from unittest.mock import patch

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")

import pygame

from games.suppression.weak_eye_key.scenes.root_scene import WeakEyeKeyScene
from games.suppression.weak_eye_key.services.board_service import WeakEyeKeyBoardService


class _DataManagerStub:
    def __init__(self):
        self.saved = []

    def save_training_session(self, payload):
        self.saved.append(payload)
        return True


class _SoundManagerStub:
    def __init__(self):
        self.correct_calls = 0
        self.wrong_calls = 0
        self.completed_calls = 0

    def play_correct(self):
        self.correct_calls += 1

    def play_wrong(self):
        self.wrong_calls += 1

    def play_completed(self):
        self.completed_calls += 1


class _ManagerStub:
    def __init__(self):
        self.settings = {"language": "en-US", "session_duration_minutes": 5}
        self.active_game_id = "suppression.weak_eye_key"
        self.active_category = "suppression"
        self.last_scene = None
        self.data_manager = _DataManagerStub()
        self.sound_manager = _SoundManagerStub()

    def t(self, key, **kwargs):
        if kwargs:
            try:
                return key.format(**kwargs)
            except Exception:
                return key
        return key

    def set_scene(self, name):
        self.last_scene = name


class WeakEyeKeySceneTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        pygame.init()

    @classmethod
    def tearDownClass(cls):
        pygame.quit()

    def test_glasses_filter_picker_can_start_session(self):
        manager = _ManagerStub()
        scene = WeakEyeKeyScene(manager)
        scene.show_filter_picker = True
        with patch("pygame.mouse.get_pos", return_value=scene.filter_start.center):
            scene.handle_events([pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=scene.filter_start.center)])
        self.assertEqual(scene.state, scene.STATE_PLAY)

    def test_correct_selection_advances_round_and_scores(self):
        manager = _ManagerStub()
        scene = WeakEyeKeyScene(manager)
        scene._start_game()
        scene.round_data = {
            "keys": [{"rect": pygame.Rect(100, 100, 74, 36), "shape": "round", "teeth": (1, 3), "color": (244, 196, 102)}],
            "target_index": 0,
            "clue": {"mode": "full", "shape": "round", "teeth": (1, 3), "color": (244, 196, 102)},
            "stage_index": 1,
        }
        scene.selected_index = 0
        scene.session.round_elapsed = 2.5
        scene._confirm_selection()
        self.assertEqual(scene.scoring.success_count, 1)
        self.assertGreater(scene.scoring.score, 0)
        self.assertEqual(manager.sound_manager.correct_calls, 1)

    def test_wrong_selection_counts_failure(self):
        manager = _ManagerStub()
        scene = WeakEyeKeyScene(manager)
        scene._start_game()
        scene.round_data = {
            "keys": [
                {"rect": pygame.Rect(100, 100, 74, 36), "shape": "round", "teeth": (1, 3), "color": (244, 196, 102)},
                {"rect": pygame.Rect(200, 100, 74, 36), "shape": "square", "teeth": (2, 1), "color": (132, 192, 255)},
            ],
            "target_index": 1,
            "clue": {"mode": "shape_only", "shape": "square", "teeth": (2, 1), "color": (132, 192, 255)},
            "stage_index": 0,
        }
        scene.selected_index = 0
        scene._confirm_selection()
        self.assertEqual(scene.scoring.failure_count, 1)
        self.assertEqual(manager.sound_manager.wrong_calls, 1)

    def test_finish_saves_result(self):
        manager = _ManagerStub()
        scene = WeakEyeKeyScene(manager)
        scene._start_game()
        scene.scoring.success_count = 3
        scene.scoring.failure_count = 1
        scene.scoring.score = 108
        scene.scoring.best_streak = 2
        scene.scoring.total_find_time = 9.0
        scene.scoring.stage_reached = 2
        scene.session.session_started_at = __import__("time").time() - scene._session_seconds()
        scene.update()
        self.assertEqual(scene.state, scene.STATE_RESULT)
        self.assertEqual(manager.data_manager.saved[-1]["game_id"], "suppression.weak_eye_key")
        self.assertEqual(manager.sound_manager.completed_calls, 1)

    def test_clue_matches_target_key(self):
        service = WeakEyeKeyBoardService()
        board_rect = pygame.Rect(64, 240, 700, 320)
        clue_rect = pygame.Rect(76, 144, 748, 84)
        round_data = service.create_round(board_rect, clue_rect, 2)
        target = round_data["keys"][round_data["target_index"]]
        clue = round_data["clue"]
        self.assertEqual(clue["shape"], target["shape"])
        self.assertEqual(clue["teeth"], target["teeth"])
        self.assertEqual(clue["color"], target["color"])
