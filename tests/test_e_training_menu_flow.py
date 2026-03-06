import os
import unittest

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")

import pygame

from scenes.config_scene import ConfigScene
from scenes.e_training_menu_scene import ETrainingMenuScene
from scenes.history_scene import HistoryScene


class _ManagerStub:
    def __init__(self, game_id="accommodation.e_orientation"):
        self.settings = {
            "start_level": 3,
            "total_questions": 30,
            "sound_enabled": True,
            "language": "en-US",
            "adaptive_enabled": True,
        }
        self.active_game_id = game_id
        self.last_scene = None
        self.data_manager = type("DM", (), {"get_all_sessions": lambda _self: []})()

    def set_scene(self, name):
        self.last_scene = name

    def t(self, key, **kwargs):
        if kwargs:
            try:
                return key.format(**kwargs)
            except Exception:
                return key
        return key

    def apply_language_preference(self):
        pass

    def apply_sound_preference(self):
        pass

    def save_user_preferences(self):
        return True


class ETrainingMenuFlowTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        pygame.init()

    @classmethod
    def tearDownClass(cls):
        pygame.quit()

    def test_e_training_menu_routes(self):
        manager = _ManagerStub()
        scene = ETrainingMenuScene(manager)

        scene.handle_events([pygame.event.Event(pygame.KEYDOWN, key=pygame.K_1)])
        self.assertEqual(manager.last_scene, "training")
        scene.handle_events([pygame.event.Event(pygame.KEYDOWN, key=pygame.K_2)])
        self.assertEqual(manager.last_scene, "config")
        scene.handle_events([pygame.event.Event(pygame.KEYDOWN, key=pygame.K_3)])
        self.assertEqual(manager.last_scene, "history")
        scene.handle_events([pygame.event.Event(pygame.KEYDOWN, key=pygame.K_ESCAPE)])
        self.assertEqual(manager.last_scene, "category")

    def test_config_and_history_return_to_game_host(self):
        manager = _ManagerStub()

        config_scene = ConfigScene(manager)
        config_scene.on_enter()
        config_scene._cancel_changes()
        self.assertEqual(manager.last_scene, "game_host")

        history_scene = HistoryScene(manager)
        history_scene.on_enter()
        history_scene.handle_events([pygame.event.Event(pygame.KEYDOWN, key=pygame.K_ESCAPE)])
        self.assertEqual(manager.last_scene, "game_host")


if __name__ == "__main__":
    unittest.main()
