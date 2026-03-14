import os
import time
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


class ProductizedGamesTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        pygame.init()

    @classmethod
    def tearDownClass(cls):
        pygame.quit()

    def test_sample_games_support_help_start_and_result_save(self):
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
            help_pos = scene.btn_help.center if hasattr(scene, "btn_help") else (0, 0)
            scene.handle_events([pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=help_pos)])
            self.assertEqual(scene.state, scene.STATE_HELP)
            scene.handle_events([pygame.event.Event(pygame.KEYDOWN, key=pygame.K_RETURN)])
            self.assertEqual(scene.state, scene.STATE_HOME)
            start_pos = scene.btn_start.center if hasattr(scene, "btn_start") else scene.btn_naked.center
            scene.handle_events([pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=start_pos)])
            self.assertEqual(scene.state, scene.STATE_PLAY)
            scene.session.session_started_at = time.time() - scene._session_seconds()
            scene.update()
            self.assertEqual(scene.state, scene.STATE_RESULT)
            self.assertEqual(manager.data_manager.saved[-1]["game_id"], descriptor.game_id)
            self.assertIn("training_metrics", manager.data_manager.saved[-1])
            self.assertEqual(manager.sound_manager.completed_calls, 1)

    def test_catch_fruit_supports_keyboard_hold_move_and_auto_catch(self):
        descriptor = build_catch_fruit_descriptor()
        manager = _ManagerStub(descriptor.game_id, descriptor.category)
        scene = descriptor.factory(manager)
        scene._start_game()
        initial_x = scene.round_data["basket_x"]
        scene.handle_events([pygame.event.Event(pygame.KEYDOWN, key=pygame.K_LEFT)])
        scene.update()
        self.assertLess(scene.round_data["basket_x"], initial_x)
        scene.handle_events([pygame.event.Event(pygame.KEYUP, key=pygame.K_LEFT)])
        scene.round_data["fruit_x"] = scene.round_data["basket_x"]
        scene.round_data["fruit_y"] = scene.play_area.bottom - 45
        scene.update()
        self.assertEqual(scene.scoring.success_count, 1)

    def test_precision_aim_supports_keyboard_aim_and_space_fire(self):
        descriptor = build_precision_aim_descriptor()
        manager = _ManagerStub(descriptor.game_id, descriptor.category)
        scene = descriptor.factory(manager)
        scene._start_game()
        target_x, target_y = scene.round_data["target_center"]
        scene.round_data["aim_center"] = [target_x - 22, target_y]
        scene.handle_events([pygame.event.Event(pygame.KEYDOWN, key=pygame.K_RIGHT)])
        self.assertEqual(tuple(scene.round_data["aim_center"]), (target_x, target_y))
        scene.handle_events([pygame.event.Event(pygame.KEYDOWN, key=pygame.K_SPACE)])
        self.assertEqual(scene.scoring.success_count, 1)

    def test_result_page_contains_summary_fields_for_sample_games(self):
        for descriptor in (build_catch_fruit_descriptor(), build_precision_aim_descriptor(), build_depth_grab_descriptor()):
            manager = _ManagerStub(descriptor.game_id, descriptor.category)
            scene = descriptor.factory(manager)
            scene.handle_events([pygame.event.Event(pygame.KEYDOWN, key=pygame.K_1)])
            scene.session.session_started_at = time.time() - scene._session_seconds()
            scene.update()
            self.assertTrue(scene.final_stats)
            self.assertIn("duration", scene.final_stats)
            self.assertIn("score", scene.final_stats)


if __name__ == "__main__":
    unittest.main()
