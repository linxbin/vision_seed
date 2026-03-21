import os
import time
import unittest

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")

import pygame

from games.amblyopia.fruit_slice.scenes.root_scene import FruitSliceScene


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
        self.frame_scale = 1.0

    def t(self, key, **kwargs):
        if kwargs:
            try:
                return key.format(**kwargs)
            except Exception:
                return key
        return key

    def set_scene(self, name):
        self.last_scene = name


class FruitSliceSceneTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        pygame.init()

    @classmethod
    def tearDownClass(cls):
        pygame.quit()

    def test_start_session_from_home(self):
        scene = FruitSliceScene(_ManagerStub())
        scene.handle_events([pygame.event.Event(pygame.KEYDOWN, key=pygame.K_1)])
        self.assertEqual(scene.state, scene.STATE_PLAY)

    def test_target_hit_scores(self):
        manager = _ManagerStub()
        scene = FruitSliceScene(manager)
        scene._start_game()
        scene.round_data["is_bomb"] = False
        center = scene.round_data["center"]
        scene.handle_events([pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=center)])
        self.assertEqual(scene.scoring.success_count, 1)
        self.assertEqual(manager.sound_manager.correct_calls, 1)

    def test_bomb_hit_plays_wrong_sound(self):
        manager = _ManagerStub()
        scene = FruitSliceScene(manager)
        scene._start_game()
        scene.round_data["is_bomb"] = True
        center = scene.round_data["center"]
        scene.handle_events([pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=center)])
        self.assertEqual(manager.sound_manager.wrong_calls, 1)

    def test_finish_saves_result(self):
        manager = _ManagerStub()
        scene = FruitSliceScene(manager)
        scene._start_game()
        scene.session.session_started_at = time.time() - scene._session_seconds()
        scene.update()
        self.assertEqual(scene.state, scene.STATE_RESULT)
        self.assertEqual(manager.data_manager.saved[-1]["game_id"], "amblyopia.fruit_slice")
        self.assertEqual(manager.sound_manager.completed_calls, 1)

    def test_frame_scale_keeps_background_phase_consistent(self):
        manager = _ManagerStub()
        manager.frame_scale = 2.0
        scene = FruitSliceScene(manager)
        scene._start_game()
        initial_phase = scene.background_phase
        scene.update()
        self.assertAlmostEqual(scene.background_phase, initial_phase + 0.1)
