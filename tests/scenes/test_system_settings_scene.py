import os
import unittest

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")

import pygame

from scenes.system_settings_scene import SystemSettingsScene


class _ManagerStub:
    def __init__(self):
        self.settings = {"language": "en-US", "sound_enabled": True, "session_duration_minutes": 5}
        self.saved = 0
        self.last_scene = None

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
        self.saved += 1
        return True

    def set_scene(self, name):
        self.last_scene = name


class SystemSettingsSceneTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        pygame.init()

    @classmethod
    def tearDownClass(cls):
        pygame.quit()

    def test_shortcuts_toggle_global_settings(self):
        manager = _ManagerStub()
        scene = SystemSettingsScene(manager)
        scene.handle_events([pygame.event.Event(pygame.KEYDOWN, key=pygame.K_1)])
        scene.handle_events([pygame.event.Event(pygame.KEYDOWN, key=pygame.K_2)])
        scene.handle_events([pygame.event.Event(pygame.KEYDOWN, key=pygame.K_3)])
        self.assertFalse(manager.settings["sound_enabled"])
        self.assertEqual(manager.settings["language"], "zh-CN")
        self.assertEqual(manager.settings["session_duration_minutes"], 10)
        self.assertEqual(manager.saved, 3)

    def test_escape_returns_menu(self):
        manager = _ManagerStub()
        scene = SystemSettingsScene(manager)
        scene.handle_events([pygame.event.Event(pygame.KEYDOWN, key=pygame.K_ESCAPE)])
        self.assertEqual(manager.last_scene, "menu")


if __name__ == "__main__":
    unittest.main()
