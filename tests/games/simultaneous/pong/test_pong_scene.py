import os
import unittest
from unittest.mock import patch

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")

import pygame

from games.simultaneous.pong.scenes.root_scene import PongScene


class _DataManagerStub:
    def __init__(self):
        self.saved = []

    def save_training_session(self, payload):
        self.saved.append(payload)
        return True


class _ManagerStub:
    def __init__(self):
        self.settings = {"language": "en-US", "session_duration_minutes": 5}
        self.active_game_id = "simultaneous.pong"
        self.active_category = "simultaneous"
        self.last_scene = None
        self.data_manager = _DataManagerStub()

    def t(self, key, **kwargs):
        if kwargs:
            try:
                return key.format(**kwargs)
            except Exception:
                return key
        return key

    def set_scene(self, name):
        self.last_scene = name


class PongSceneTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        pygame.init()

    @classmethod
    def tearDownClass(cls):
        pygame.quit()

    def test_glasses_filter_picker_can_start_match(self):
        manager = _ManagerStub()
        scene = PongScene(manager)
        scene.show_filter_picker = True
        with patch("pygame.mouse.get_pos", return_value=scene.filter_start.center):
            scene.handle_events([pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=scene.filter_start.center)])
        self.assertEqual(scene.state, scene.STATE_PLAY)

    def test_match_finishes_and_saves_result(self):
        manager = _ManagerStub()
        scene = PongScene(manager)
        scene._start_match()
        scene.player_score = 11
        scene.update()
        self.assertEqual(scene.state, scene.STATE_RESULT)
        self.assertEqual(manager.data_manager.saved[-1]["game_id"], "simultaneous.pong")

    def test_keyboard_moves_player_paddle(self):
        manager = _ManagerStub()
        scene = PongScene(manager)
        scene._start_match()
        initial_y = scene.player_y
        scene.handle_events([pygame.event.Event(pygame.KEYDOWN, key=pygame.K_UP)])
        scene.update()
        self.assertLess(scene.player_y, initial_y)

    def test_player_hit_increases_rally_and_speed(self):
        manager = _ManagerStub()
        scene = PongScene(manager)
        scene._start_match()
        scene.serve_until = 0
        paddle = scene._player_paddle_rect()
        scene.ball_x = paddle.right + 8
        scene.ball_y = paddle.centery
        scene.ball_vx = -5.0
        scene.ball_vy = 0.0
        scene.update()
        self.assertGreater(scene.current_rally, 0)
        self.assertGreater(scene.ball_vx, 5.0)

    def test_match_starts_with_serve_delay(self):
        manager = _ManagerStub()
        scene = PongScene(manager)
        scene._start_match()
        self.assertGreater(scene.serve_until, scene.session_started_at)

    def test_finish_match_records_goal_and_encouragement(self):
        manager = _ManagerStub()
        scene = PongScene(manager)
        scene._start_match()
        scene.player_score = 5
        scene.ai_score = 2
        scene.best_rally = 4
        scene._finish_match()
        self.assertIn("encouragement", scene.final_stats)


if __name__ == "__main__":
    unittest.main()
