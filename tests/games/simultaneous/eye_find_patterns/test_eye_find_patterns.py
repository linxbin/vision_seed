import os
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

        scene.right_center = (420, 320)
        scene._confirm_action()
        self.assertEqual(scene.scoring.success_count, 1)
        self.assertEqual(scene.scoring.score, 10)
        self.assertEqual(scene.scoring.combo, 0)

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
        scene.handle_events([pygame.event.Event(pygame.KEYDOWN, key=pygame.K_3)])
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


if __name__ == "__main__":
    unittest.main()
