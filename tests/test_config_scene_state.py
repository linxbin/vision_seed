import os
import unittest

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")

import pygame

from scenes.config_scene import ConfigScene


class _ManagerStub:
    def __init__(self):
        self.settings = {
            "start_level": 3,
            "total_questions": 30,
            "sound_enabled": True,
            "language": "en-US",
            "adaptive_enabled": True,
        }
        self.saved = 0
        self.last_scene = None

    def apply_language_preference(self):
        pass

    def apply_sound_preference(self):
        pass

    def save_user_preferences(self):
        self.saved += 1
        return True

    def set_scene(self, name):
        self.last_scene = name

    def t(self, key, **kwargs):
        return key


class ConfigSceneStateTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        pygame.init()

    @classmethod
    def tearDownClass(cls):
        pygame.quit()

    def test_commit_uses_draft_settings(self):
        manager = _ManagerStub()
        scene = ConfigScene(manager)
        scene.on_enter()

        scene.draft_settings["start_level"] = 5
        scene.draft_settings["total_questions"] = 40
        scene.draft_settings["sound_enabled"] = False
        scene.draft_settings["language"] = "zh-CN"
        scene.draft_settings["adaptive_enabled"] = False
        scene._commit_settings()

        self.assertEqual(manager.settings["start_level"], 5)
        self.assertEqual(manager.settings["total_questions"], 40)
        self.assertFalse(manager.settings["sound_enabled"])
        self.assertEqual(manager.settings["language"], "zh-CN")
        self.assertFalse(manager.settings["adaptive_enabled"])
        self.assertEqual(manager.saved, 1)

    def test_cancel_restores_original_settings(self):
        manager = _ManagerStub()
        scene = ConfigScene(manager)
        scene.on_enter()

        scene.draft_settings["start_level"] = 7
        scene.draft_settings["total_questions"] = 100
        scene.draft_settings["sound_enabled"] = False
        scene.draft_settings["language"] = "zh-CN"
        scene.draft_settings["adaptive_enabled"] = False
        scene._apply_live_preferences()
        scene._cancel_changes()

        self.assertEqual(manager.settings["start_level"], 3)
        self.assertEqual(manager.settings["total_questions"], 30)
        self.assertTrue(manager.settings["sound_enabled"])
        self.assertEqual(manager.settings["language"], "en-US")
        self.assertTrue(manager.settings["adaptive_enabled"])
        self.assertEqual(manager.last_scene, "menu")

    def test_feedback_message_set_on_commit_and_validation_error(self):
        manager = _ManagerStub()
        scene = ConfigScene(manager)
        scene.on_enter()

        scene._commit_settings()
        self.assertEqual(scene.feedback_variant, "success")
        self.assertTrue(scene.feedback_message)

        scene.input_text = "abc"
        ok = scene._validate_and_update_questions(allow_empty=True)
        self.assertFalse(ok)
        self.assertEqual(scene.feedback_variant, "error")
        self.assertTrue(scene.feedback_message)

    def test_ctrl_s_commits_and_returns_menu(self):
        manager = _ManagerStub()
        scene = ConfigScene(manager)
        scene.on_enter()

        scene.draft_settings["total_questions"] = 44
        scene.input_text = "44"
        event = pygame.event.Event(pygame.KEYDOWN, key=pygame.K_s, mod=pygame.KMOD_CTRL, unicode="")
        scene.handle_events([event])

        self.assertEqual(manager.settings["total_questions"], 44)
        self.assertEqual(manager.last_scene, "menu")
        self.assertEqual(manager.saved, 1)

    def test_enter_with_invalid_input_does_not_commit_or_start(self):
        manager = _ManagerStub()
        scene = ConfigScene(manager)
        scene.on_enter()

        scene.input_text = "abc"
        event = pygame.event.Event(pygame.KEYDOWN, key=pygame.K_RETURN, mod=0, unicode="\r")
        scene.handle_events([event])

        self.assertEqual(manager.settings["total_questions"], 30)
        self.assertIsNone(manager.last_scene)
        self.assertEqual(manager.saved, 0)
        self.assertTrue(scene.input_error)

    def test_ctrl_s_with_invalid_input_does_not_commit_or_leave(self):
        manager = _ManagerStub()
        scene = ConfigScene(manager)
        scene.on_enter()

        scene.input_text = "abc"
        event = pygame.event.Event(pygame.KEYDOWN, key=pygame.K_s, mod=pygame.KMOD_CTRL, unicode="")
        scene.handle_events([event])

        self.assertEqual(manager.settings["total_questions"], 30)
        self.assertIsNone(manager.last_scene)
        self.assertEqual(manager.saved, 0)
        self.assertTrue(scene.input_error)

    def test_escape_cancels_and_rolls_back(self):
        manager = _ManagerStub()
        scene = ConfigScene(manager)
        scene.on_enter()

        scene.draft_settings["sound_enabled"] = False
        scene._apply_live_preferences()
        self.assertFalse(manager.settings["sound_enabled"])

        event = pygame.event.Event(pygame.KEYDOWN, key=pygame.K_ESCAPE, mod=0, unicode="")
        scene.handle_events([event])

        self.assertTrue(manager.settings["sound_enabled"])
        self.assertEqual(manager.last_scene, "menu")
        self.assertEqual(manager.saved, 0)

    def test_toggle_shortcuts_sync_draft_and_manager(self):
        manager = _ManagerStub()
        scene = ConfigScene(manager)
        scene.on_enter()

        events = [
            pygame.event.Event(pygame.KEYDOWN, key=pygame.K_m, mod=0, unicode="m"),
            pygame.event.Event(pygame.KEYDOWN, key=pygame.K_l, mod=0, unicode="l"),
            pygame.event.Event(pygame.KEYDOWN, key=pygame.K_a, mod=0, unicode="a"),
        ]
        scene.handle_events(events)

        self.assertFalse(scene.draft_settings["sound_enabled"])
        self.assertEqual(scene.draft_settings["language"], "zh-CN")
        self.assertFalse(scene.draft_settings["adaptive_enabled"])
        self.assertFalse(manager.settings["sound_enabled"])
        self.assertEqual(manager.settings["language"], "zh-CN")
        self.assertFalse(manager.settings["adaptive_enabled"])

    def test_level_arrow_keys_clamp_to_bounds(self):
        manager = _ManagerStub()
        scene = ConfigScene(manager)
        scene.on_enter()
        scene.draft_settings["start_level"] = 1

        up_event = pygame.event.Event(pygame.KEYDOWN, key=pygame.K_UP, mod=0, unicode="")
        scene.handle_events([up_event])
        self.assertEqual(scene.draft_settings["start_level"], 1)

        for _ in range(30):
            down_event = pygame.event.Event(pygame.KEYDOWN, key=pygame.K_DOWN, mod=0, unicode="")
            scene.handle_events([down_event])
        self.assertEqual(scene.draft_settings["start_level"], 10)


if __name__ == "__main__":
    unittest.main()
