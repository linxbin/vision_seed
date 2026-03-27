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

    def test_duration_cycles_only_supported_presets(self):
        manager = _ManagerStub()
        manager.settings["session_duration_minutes"] = 1
        scene = SystemSettingsScene(manager)
        scene._cycle_session_duration()
        self.assertEqual(manager.settings["session_duration_minutes"], 3)
        scene._cycle_session_duration()
        self.assertEqual(manager.settings["session_duration_minutes"], 5)
        scene._cycle_session_duration()
        self.assertEqual(manager.settings["session_duration_minutes"], 10)
        scene._cycle_session_duration()
        self.assertEqual(manager.settings["session_duration_minutes"], 1)

    def test_escape_returns_menu(self):
        manager = _ManagerStub()
        scene = SystemSettingsScene(manager)
        scene.handle_events([pygame.event.Event(pygame.KEYDOWN, key=pygame.K_ESCAPE)])
        self.assertEqual(manager.last_scene, "menu")

    def test_focus_navigation_and_enter_activate_items(self):
        manager = _ManagerStub()
        scene = SystemSettingsScene(manager)
        scene.handle_events([pygame.event.Event(pygame.KEYDOWN, key=pygame.K_DOWN)])
        self.assertEqual(scene.focused_index, 1)
        scene.handle_events([pygame.event.Event(pygame.KEYDOWN, key=pygame.K_RETURN)])
        self.assertEqual(manager.settings["language"], "zh-CN")
        scene.handle_events([pygame.event.Event(pygame.KEYDOWN, key=pygame.K_UP)])
        self.assertEqual(scene.focused_index, 0)
        scene.handle_events([pygame.event.Event(pygame.KEYDOWN, key=pygame.K_SPACE)])
        self.assertFalse(manager.settings["sound_enabled"])


if __name__ == "__main__":
    unittest.main()
