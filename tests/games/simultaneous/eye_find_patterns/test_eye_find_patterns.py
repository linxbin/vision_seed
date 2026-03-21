import os
import time
import unittest
from unittest.mock import patch

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")

import pygame

from games.simultaneous.eye_find_patterns.scenes.game_scene import EyeFindPatternsScene
from games.simultaneous.eye_find_patterns.services.scoring_service import EyeFindScoringService


class _ManagerStub:
    def __init__(self):
        self.settings = {"language": "en-US", "session_duration_minutes": 5}
        self.active_game_id = "simultaneous.eye_find_patterns"
        self.active_category = "simultaneous"
        self.last_scene = None
        self.sound_manager = type(
            "SoundManager",
            (),
            {
                "__init__": lambda self: setattr(self, "calls", {"correct": 0, "wrong": 0, "completed": 0}),
                "play_correct": lambda self: self.calls.__setitem__("correct", self.calls["correct"] + 1),
                "play_wrong": lambda self: self.calls.__setitem__("wrong", self.calls["wrong"] + 1),
                "play_completed": lambda self: self.calls.__setitem__("completed", self.calls["completed"] + 1),
            },
        )()

    def t(self, key, **kwargs):
        if kwargs:
            try:
                return key.format(**kwargs)
            except Exception:
                return key
        return key

    def set_scene(self, name):
        self.last_scene = name


class EyeFindPatternsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        pygame.init()

    @classmethod
    def tearDownClass(cls):
        pygame.quit()

    def test_scoring_combo_bonus(self):
        scoring = EyeFindScoringService()
        g1 = scoring.on_success()
        g2 = scoring.on_success()
        g3 = scoring.on_success()
        self.assertEqual(g1, 10)
        self.assertEqual(g2, 10)
        self.assertEqual(g3, 30)
        self.assertEqual(scoring.score, 50)
        self.assertEqual(scoring.success_count, 3)

    def test_confirm_success_and_failure(self):
        manager = _ManagerStub()
        scene = EyeFindPatternsScene(manager)
        scene._start_game()
        scene.left_center = (320, 320)
        scene.right_center = (320, 320)
        scene._confirm_action()
        self.assertEqual(scene.scoring.success_count, 1)
        self.assertEqual(scene.scoring.score, 10)
        self.assertEqual(manager.sound_manager.calls["correct"], 1)

        scene.right_center = (420, 320)
        scene._confirm_action()
        self.assertEqual(scene.scoring.success_count, 1)
        self.assertEqual(scene.scoring.score, 10)
        self.assertEqual(scene.scoring.combo, 0)
        self.assertEqual(manager.sound_manager.calls["wrong"], 1)

    def test_home_button_exit_to_main_menu(self):
        manager = _ManagerStub()
        scene = EyeFindPatternsScene(manager)
        scene._start_game()
        x = scene.btn_home.centerx
        y = scene.btn_home.centery
        event = pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=(x, y))
        with patch("pygame.mouse.get_pos", return_value=(x, y)):
            scene.handle_events([event])
        self.assertEqual(manager.last_scene, "menu")

    def test_glasses_mode_can_start(self):
        manager = _ManagerStub()
        scene = EyeFindPatternsScene(manager)
        scene.show_filter_picker = True
        x = scene.filter_start.centerx
        y = scene.filter_start.centery
        event = pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=(x, y))
        with patch("pygame.mouse.get_pos", return_value=(x, y)):
            scene.handle_events([event])
        self.assertEqual(scene.state, scene.STATE_PLAY)

    def test_help_page_navigation(self):
        manager = _ManagerStub()
        scene = EyeFindPatternsScene(manager)
        scene.state = scene.STATE_HOME
        scene.handle_events([pygame.event.Event(pygame.KEYDOWN, key=pygame.K_2)])
        self.assertEqual(scene.state, scene.STATE_HELP)
        x = scene.help_ok.centerx
        y = scene.help_ok.centery
        event = pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=(x, y))
        with patch("pygame.mouse.get_pos", return_value=(x, y)):
            scene.handle_events([event])
        self.assertEqual(scene.state, scene.STATE_HOME)

    def test_glasses_mode_uses_configured_background_color_in_play(self):
        manager = _ManagerStub()
        scene = EyeFindPatternsScene(manager)
        scene.mode = scene.MODE_GLASSES
        scene._start_game()
        scene.mode = scene.MODE_GLASSES
        screen = pygame.Surface((scene.width, scene.height))
        scene.draw(screen)
        self.assertEqual(screen.get_at((4, 4))[:3], (248, 86, 255))

    def test_session_seconds_follow_global_settings(self):
        manager = _ManagerStub()
        manager.settings["session_duration_minutes"] = 10
        scene = EyeFindPatternsScene(manager)
        self.assertEqual(scene._session_seconds(), 600)

    def test_play_scene_renders_after_resize(self):
        scene = EyeFindPatternsScene(_ManagerStub())
        scene._start_game()
        scene.on_resize(840, 640)
        surface = pygame.Surface((840, 640))
        scene.draw(surface)
        self.assertGreater(sum(surface.get_at((420, 320))[:3]), 0)

    def test_drag_render_uses_local_blend_bounds(self):
        scene = EyeFindPatternsScene(_ManagerStub())
        scene._start_game()
        scene.left_center = (320, 320)
        scene.right_center = (420, 320)
        surface = pygame.Surface((scene.width, scene.height))
        captured = {}

        def _capture(canvas_size, left_surface, left_rect, right_surface, right_rect, crop_border=0, use_offset_crop=True):
            captured["canvas_size"] = canvas_size
            merged = pygame.Surface(canvas_size, pygame.SRCALPHA)
            merged.blit(left_surface, left_rect)
            merged.blit(right_surface, right_rect)
            return merged

        with patch.object(scene.pattern_service, "blend_filtered_patterns", side_effect=_capture):
            scene.draw(surface)
        self.assertLess(captured["canvas_size"][0], scene.width)
        self.assertLess(captured["canvas_size"][1], scene.height)

    def test_play_scene_draws_visible_patterns(self):
        scene = EyeFindPatternsScene(_ManagerStub())
        scene._start_game()
        scene.left_center = (320, 320)
        scene.right_center = (420, 320)
        surface = pygame.Surface((scene.width, scene.height), pygame.SRCALPHA)
        scene.draw(surface)
        left_sample = surface.get_at((320, 320))
        right_sample = surface.get_at((420, 320))
        self.assertGreater(left_sample[3], 0)
        self.assertGreater(right_sample[3], 0)

    def test_finish_game_plays_completed_sound(self):
        manager = _ManagerStub()
        scene = EyeFindPatternsScene(manager)
        scene._start_game()
        scene.session.session_started_at = time.time() - scene._session_seconds()
        scene.update()
        self.assertEqual(scene.state, scene.STATE_RESULT)
        self.assertEqual(manager.sound_manager.calls["completed"], 1)


if __name__ == "__main__":
    unittest.main()
