import os
import time
import unittest
from unittest.mock import patch

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")

import pygame

from games.fusion.tetris.scenes.root_scene import FusionTetrisScene


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
        self.data_manager = _DataManagerStub()
        self.sound_manager = _SoundManagerStub()
        self.last_scene = None

    def t(self, key, **kwargs):
        if kwargs:
            try:
                return key.format(**kwargs)
            except Exception:
                return key
        return key

    def set_scene(self, name):
        self.last_scene = name


class FusionTetrisSceneTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        pygame.init()

    @classmethod
    def tearDownClass(cls):
        pygame.quit()

    def test_glasses_mode_can_start(self):
        scene = FusionTetrisScene(_ManagerStub())
        scene.show_filter_picker = True
        with patch("pygame.mouse.get_pos", return_value=scene.filter_start.center):
            scene.handle_events([pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=scene.filter_start.center)])
        self.assertEqual(scene.state, scene.STATE_PLAY)

    def test_lock_piece_updates_score_or_moves(self):
        manager = _ManagerStub()
        scene = FusionTetrisScene(manager)
        scene._start_game()
        rows = scene.round_data["rows"]
        cols = scene.round_data["cols"]
        scene.round_data["stack"] = [(x, rows - 1) for x in range(cols) if x not in (0, 1)]
        scene.round_data["piece"] = [(0, 0), (1, 0)]
        scene.round_data["piece_x"] = 0
        scene.round_data["piece_y"] = rows - 1
        scene._lock_piece()
        self.assertGreaterEqual(scene.scoring.moves, 1)
        self.assertEqual(manager.sound_manager.correct_calls, 1)

    def test_glasses_filter_direction_changes_render(self):
        scene = FusionTetrisScene(_ManagerStub())
        scene._start_game()
        scene.mode = scene.MODE_GLASSES
        first = pygame.Surface((scene.width, scene.height), pygame.SRCALPHA)
        second = pygame.Surface((scene.width, scene.height), pygame.SRCALPHA)
        scene.filter_direction = "left_red_right_blue"
        scene.draw(first)
        scene.filter_direction = "left_blue_right_red"
        scene.draw(second)
        self.assertNotEqual(pygame.image.tostring(first, "RGBA"), pygame.image.tostring(second, "RGBA"))

    def test_finish_saves_result(self):
        manager = _ManagerStub()
        scene = FusionTetrisScene(manager)
        scene._start_game()
        scene.session.session_started_at = time.time() - scene._session_seconds()
        scene.update()
        self.assertEqual(scene.state, scene.STATE_RESULT)
        self.assertEqual(manager.data_manager.saved[-1]["game_id"], "fusion.tetris")
        self.assertEqual(manager.sound_manager.completed_calls, 1)
