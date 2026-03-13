import os
import unittest

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")

import pygame

from games.accommodation.catch_fruit.game import build_descriptor as build_catch_fruit_descriptor
from games.amblyopia.precision_aim.game import build_descriptor as build_precision_aim_descriptor
from games.stereopsis.depth_grab.game import build_descriptor as build_depth_grab_descriptor
from games.suppression.weak_eye_key.game import build_descriptor as build_weak_eye_key_descriptor


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
        return 0.0


class _ManagerStub:
    def __init__(self, game_id, category):
        self.settings = {"language": "en-US", "session_duration_minutes": 5}
        self.active_game_id = game_id
        self.active_category = category
        self.screen_size = (900, 700)
        self.current_result = {}
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


class ArcadeTrainingGamesTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        pygame.init()

    @classmethod
    def tearDownClass(cls):
        pygame.quit()

    def test_all_benchmark_games_support_help_start_and_result_save(self):
        descriptors = [
            build_catch_fruit_descriptor(),
            build_weak_eye_key_descriptor(),
            build_depth_grab_descriptor(),
            build_precision_aim_descriptor(),
        ]
        surface = pygame.Surface((900, 700))
        for descriptor in descriptors:
            manager = _ManagerStub(descriptor.game_id, descriptor.category)
            scene = descriptor.factory(manager)
            scene.on_resize(900, 700)
            scene.draw(surface)
            scene.handle_events([pygame.event.Event(pygame.KEYDOWN, key=pygame.K_2)])
            self.assertEqual(scene.state, scene.STATE_HELP)
            scene.handle_events([pygame.event.Event(pygame.KEYDOWN, key=pygame.K_RETURN)])
            self.assertEqual(scene.state, scene.STATE_HOME)
            scene.handle_events([pygame.event.Event(pygame.KEYDOWN, key=pygame.K_1)])
            self.assertEqual(scene.state, scene.STATE_PLAY)
            scene.mechanic.outcome = True
            scene.update()
            self.assertEqual(scene.state, scene.STATE_PLAY)
            scene.session_started_at = __import__("time").time() - scene._session_seconds()
            scene.update()
            self.assertEqual(scene.state, scene.STATE_RESULT)
            self.assertEqual(manager.data_manager.saved[-1]["game_id"], descriptor.game_id)
            self.assertIn("training_metrics", manager.data_manager.saved[-1])
            self.assertEqual(manager.sound_manager.correct_calls, 1)
            self.assertEqual(manager.sound_manager.completed_calls, 1)

    def test_catch_fruit_supports_keyboard_hold_move_and_auto_catch(self):
        descriptor = build_catch_fruit_descriptor()
        manager = _ManagerStub(descriptor.game_id, descriptor.category)
        scene = descriptor.factory(manager)
        scene._start_session()
        mechanic = scene.mechanic
        initial_x = mechanic.basket_x
        scene.handle_events([pygame.event.Event(pygame.KEYDOWN, key=pygame.K_LEFT)])
        mechanic.update(0.0)
        self.assertLess(mechanic.basket_x, initial_x)
        scene.handle_events([pygame.event.Event(pygame.KEYUP, key=pygame.K_LEFT)])
        mechanic.fruit_x = mechanic.basket_x
        mechanic.fruit_y = scene.play_area.bottom - 45
        mechanic.update(0.0)
        self.assertTrue(mechanic.outcome)

    def test_precision_aim_supports_keyboard_aim_and_space_fire(self):
        descriptor = build_precision_aim_descriptor()
        manager = _ManagerStub(descriptor.game_id, descriptor.category)
        scene = descriptor.factory(manager)
        scene._start_session()
        mechanic = scene.mechanic
        target_x, target_y = mechanic.target_center
        mechanic.aim_center = [target_x - 22, target_y]
        scene.handle_events([pygame.event.Event(pygame.KEYDOWN, key=pygame.K_RIGHT)])
        self.assertEqual(tuple(mechanic.aim_center), (target_x, target_y))
        scene.handle_events([pygame.event.Event(pygame.KEYDOWN, key=pygame.K_SPACE)])
        self.assertTrue(mechanic.outcome)

    def test_result_page_contains_reward_fields_for_sample_games(self):
        for descriptor in (build_catch_fruit_descriptor(), build_precision_aim_descriptor()):
            manager = _ManagerStub(descriptor.game_id, descriptor.category)
            scene = descriptor.factory(manager)
            scene._start_session()
            scene.mechanic.outcome = True
            scene.update()
            scene.session_started_at = __import__("time").time() - scene._session_seconds()
            scene.update()
            self.assertIn("reward_summary", scene.final_stats)
            self.assertIn("next_goal", scene.final_stats)
            self.assertIn("stars", scene.final_stats)


if __name__ == "__main__":
    unittest.main()
