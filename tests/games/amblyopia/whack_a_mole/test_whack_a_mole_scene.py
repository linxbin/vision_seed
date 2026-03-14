import os
import time
import unittest

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")

import pygame

from games.amblyopia.whack_a_mole.scenes.root_scene import WhackAMoleScene


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


class WhackAMoleSceneTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        pygame.init()

    @classmethod
    def tearDownClass(cls):
        pygame.quit()

    def test_start_session_from_home(self):
        scene = WhackAMoleScene(_ManagerStub())
        scene.handle_events([pygame.event.Event(pygame.KEYDOWN, key=pygame.K_1)])
        self.assertEqual(scene.state, scene.STATE_PLAY)

    def test_center_hit_scores(self):
        manager = _ManagerStub()
        scene = WhackAMoleScene(manager)
        scene._start_game()
        pos = scene.round_data["target_center"]
        scene.session.round_started_at = time.time() - 1.0
        scene.session.tick(time.time())
        scene._handle_hit(pos)
        self.assertEqual(scene.scoring.success_count, 1)
        self.assertGreater(scene.scoring.score, 0)
        self.assertEqual(manager.sound_manager.correct_calls, 1)

    def test_timeout_counts_failure(self):
        manager = _ManagerStub()
        scene = WhackAMoleScene(manager)
        scene._start_game()
        scene.session.round_started_at = time.time() - scene.session.ROUND_SECONDS
        scene.update()
        self.assertGreaterEqual(scene.scoring.failure_count, 1)
        self.assertEqual(manager.sound_manager.wrong_calls, 1)

    def test_finish_saves_result(self):
        manager = _ManagerStub()
        scene = WhackAMoleScene(manager)
        scene._start_game()
        scene.session.session_started_at = time.time() - scene._session_seconds()
        scene.update()
        self.assertEqual(scene.state, scene.STATE_RESULT)
        self.assertEqual(manager.data_manager.saved[-1]["game_id"], "amblyopia.whack_a_mole")
        self.assertEqual(manager.sound_manager.completed_calls, 1)
