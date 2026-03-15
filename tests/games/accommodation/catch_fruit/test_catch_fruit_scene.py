import os
import time
import unittest

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")

import pygame

from games.accommodation.catch_fruit.scenes.root_scene import CatchFruitScene


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


class CatchFruitSceneTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        pygame.init()

    @classmethod
    def tearDownClass(cls):
        pygame.quit()

    def test_start_session_from_home(self):
        scene = CatchFruitScene(_ManagerStub())
        scene.handle_events([pygame.event.Event(pygame.KEYDOWN, key=pygame.K_1)])
        self.assertEqual(scene.state, scene.STATE_PLAY)

    def test_successful_catch_scores(self):
        manager = _ManagerStub()
        scene = CatchFruitScene(manager)
        scene._start_game()
        fruit = scene.round_data["fruits"][0]
        fruit.update({"x": 200, "y": scene.play_area.bottom - 46, "fruit_name": "apple"})
        scene.round_data["basket_x"] = 200
        scene._resolve_catch(True, fruit)
        self.assertEqual(scene.scoring.success_count, 1)
        self.assertGreater(scene.scoring.score, 0)
        self.assertEqual(manager.sound_manager.correct_calls, 1)

    def test_successful_catch_keeps_basket_position(self):
        scene = CatchFruitScene(_ManagerStub())
        scene._start_game()
        fruit = scene.round_data["fruits"][0]
        fruit.update({"x": 260, "y": scene.play_area.bottom - 46, "fruit_name": "apple"})
        scene.round_data["basket_x"] = 260
        scene._resolve_catch(True, fruit)
        self.assertEqual(scene.round_data["basket_x"], 260)

    def test_miss_counts_failure(self):
        manager = _ManagerStub()
        scene = CatchFruitScene(manager)
        scene._start_game()
        scene._resolve_catch(False, scene.round_data["fruits"][0])
        self.assertEqual(scene.scoring.failure_count, 1)
        self.assertEqual(manager.sound_manager.wrong_calls, 1)

    def test_round_spawns_multiple_fruits(self):
        scene = CatchFruitScene(_ManagerStub())
        scene._start_game()
        self.assertGreaterEqual(len(scene.round_data["fruits"]), 2)

    def test_finish_saves_result(self):
        manager = _ManagerStub()
        scene = CatchFruitScene(manager)
        scene._start_game()
        scene.scoring.success_count = 3
        scene.scoring.failure_count = 1
        scene.scoring.score = 46
        scene.session.session_started_at = time.time() - scene._session_seconds()
        scene.update()
        self.assertEqual(scene.state, scene.STATE_RESULT)
        self.assertEqual(manager.data_manager.saved[-1]["game_id"], "accommodation.catch_fruit")
        self.assertEqual(manager.sound_manager.completed_calls, 1)
