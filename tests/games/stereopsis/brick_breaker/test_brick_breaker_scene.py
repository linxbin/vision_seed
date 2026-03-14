import os
import time
import unittest
from unittest.mock import patch

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")

import pygame

from games.stereopsis.brick_breaker.scenes.root_scene import BrickBreakerScene


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


class BrickBreakerSceneTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        pygame.init()

    @classmethod
    def tearDownClass(cls):
        pygame.quit()

    def test_glasses_mode_can_start(self):
        scene = BrickBreakerScene(_ManagerStub())
        scene.show_filter_picker = True
        with patch("pygame.mouse.get_pos", return_value=scene.filter_start.center):
            scene.handle_events([pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=scene.filter_start.center)])
        self.assertEqual(scene.state, scene.STATE_PLAY)

    def test_brick_hit_scores(self):
        scene = BrickBreakerScene(_ManagerStub())
        scene._start_game()
        brick = scene.round_data["bricks"][0]
        scene.round_data["ball"] = [brick["rect"][0] + brick["rect"][2] // 2, brick["rect"][1] + brick["rect"][3] // 2]
        scene.round_data["velocity"] = [0, 0]
        scene.update()
        self.assertGreaterEqual(scene.scoring.brick_count, 1)

    def test_finish_saves_result(self):
        manager = _ManagerStub()
        scene = BrickBreakerScene(manager)
        scene._start_game()
        scene.session.session_started_at = time.time() - scene._session_seconds()
        scene.update()
        self.assertEqual(scene.state, scene.STATE_RESULT)
        self.assertEqual(manager.data_manager.saved[-1]["game_id"], "stereopsis.brick_breaker")
