import os
import unittest

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")

import pygame

from games.accommodation.e_orientation.scenes.root_scene import ETrainingRootScene


class _SoundStub:
    def play_correct(self):
        pass

    def play_wrong(self):
        pass

    def play_completed(self):
        return 0.0

    def set_enabled(self, _enabled):
        pass


class _DataStub:
    def get_all_sessions(self):
        return []

    def save_training_session(self, _session):
        return True


class _RootManagerStub:
    def __init__(self):
        self.settings = {
            "start_level": 3,
            "total_questions": 5,
            "sound_enabled": False,
            "language": "en-US",
            "adaptive_enabled": True,
        }
        self.current_result = {"correct": 0, "wrong": 0, "total": 0, "duration": 0.0, "max_combo": 0, "game_id": "accommodation.e_orientation"}
        self.sound_manager = _SoundStub()
        self.data_manager = _DataStub()
        self.screen_size = (900, 700)
        self.active_game_id = "accommodation.e_orientation"
        self.last_scene = None

    def set_scene(self, name):
        self.last_scene = name

    def t(self, key, **kwargs):
        if kwargs:
            try:
                return key.format(**kwargs)
            except Exception:
                return key
        return key

    def apply_sound_preference(self):
        pass

    def apply_language_preference(self):
        pass

    def save_user_preferences(self):
        return True

    def evaluate_adaptive_level(self):
        return {"reason_code": "DISABLED"}


class ETrainingRootSceneTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        pygame.init()

    @classmethod
    def tearDownClass(cls):
        pygame.quit()

    def test_local_menu_routes_stay_inside_root_scene(self):
        manager = _RootManagerStub()
        scene = ETrainingRootScene(manager)
        scene.reset()

        scene.handle_events([pygame.event.Event(pygame.KEYDOWN, key=pygame.K_1)])
        self.assertEqual(scene.current_scene_name, "training")
        self.assertIsNone(manager.last_scene)

        scene.current_scene.handle_events([pygame.event.Event(pygame.KEYDOWN, key=pygame.K_ESCAPE)])
        self.assertEqual(scene.current_scene_name, "menu")
        self.assertIsNone(manager.last_scene)

    def test_global_route_still_uses_real_manager(self):
        manager = _RootManagerStub()
        scene = ETrainingRootScene(manager)
        scene.reset()

        scene.handle_events([pygame.event.Event(pygame.KEYDOWN, key=pygame.K_ESCAPE)])
        self.assertEqual(manager.last_scene, "category")


if __name__ == "__main__":
    unittest.main()
