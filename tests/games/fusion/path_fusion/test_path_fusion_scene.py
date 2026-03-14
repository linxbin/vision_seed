import os
import time
import unittest
from unittest.mock import patch

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")

import pygame

from games.fusion.path_fusion.scenes.root_scene import PathFusionScene


class _DataManagerStub:
    def __init__(self):
        self.saved = []

    def save_training_session(self, payload):
        self.saved.append(payload)
        return True


class _ManagerStub:
    def __init__(self):
        self.settings = {"language": "en-US", "session_duration_minutes": 5}
        self.data_manager = _DataManagerStub()
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


class PathFusionSceneTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        pygame.init()

    @classmethod
    def tearDownClass(cls):
        pygame.quit()

    def test_glasses_mode_can_start(self):
        scene = PathFusionScene(_ManagerStub())
        scene.show_filter_picker = True
        with patch("pygame.mouse.get_pos", return_value=scene.filter_start.center):
            scene.handle_events([pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=scene.filter_start.center)])
        self.assertEqual(scene.state, scene.STATE_PLAY)

    def test_correct_path_scores(self):
        scene = PathFusionScene(_ManagerStub())
        scene._start_game()
        scene.selected_path = scene.round_data["target"]
        scene.handle_events([pygame.event.Event(pygame.KEYDOWN, key=pygame.K_RETURN)])
        self.assertEqual(scene.scoring.success_count, 1)

    def test_finish_saves_result(self):
        manager = _ManagerStub()
        scene = PathFusionScene(manager)
        scene._start_game()
        scene.session.session_started_at = time.time() - scene._session_seconds()
        scene.update()
        self.assertEqual(scene.state, scene.STATE_RESULT)
        self.assertEqual(manager.data_manager.saved[-1]["game_id"], "fusion.path_fusion")
