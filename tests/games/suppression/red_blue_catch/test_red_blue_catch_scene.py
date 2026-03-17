import os
import time
import unittest
from unittest.mock import patch

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")

import pygame

from games.suppression.red_blue_catch.scenes.root_scene import RedBlueCatchScene


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


class _ManagerStub:
    def __init__(self):
        self.settings = {"language": "en-US", "session_duration_minutes": 5}
        self.data_manager = _DataManagerStub()
        self.sound_manager = _SoundManagerStub()
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


class RedBlueCatchSceneTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        pygame.init()

    @classmethod
    def tearDownClass(cls):
        pygame.quit()

    def test_glasses_mode_can_start(self):
        scene = RedBlueCatchScene(_ManagerStub())
        scene.show_filter_picker = True
        with patch("pygame.mouse.get_pos", return_value=scene.filter_start.center):
            scene.handle_events([pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=scene.filter_start.center)])
        self.assertEqual(scene.state, scene.STATE_PLAY)

    def test_play_back_button_returns_to_menu(self):
        manager = _ManagerStub()
        scene = RedBlueCatchScene(manager)
        scene._start_game()
        scene.handle_events([pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=scene.btn_home.center)])
        self.assertEqual(manager.last_scene, "menu")

    def test_reset_returns_to_home_and_clears_glasses_state(self):
        scene = RedBlueCatchScene(_ManagerStub())
        scene.mode = scene.MODE_GLASSES
        scene.state = scene.STATE_PLAY
        scene.show_filter_picker = True
        scene.reset()
        self.assertEqual(scene.state, scene.STATE_HOME)
        self.assertEqual(scene.mode, scene.MODE_GLASSES)
        self.assertFalse(scene.show_filter_picker)

    def test_correct_catch_scores(self):
        manager = _ManagerStub()
        scene = RedBlueCatchScene(manager)
        scene._start_game()
        ball = scene.round_data["balls"][0]
        ball["x"] = scene.round_data["basket_x"]
        ball["y"] = scene.play_area.bottom - 28
        scene.update()
        self.assertEqual(scene.scoring.success_count, 1)
        self.assertEqual(manager.sound_manager.correct_calls, 1)

    def test_round_spawns_multiple_balls(self):
        scene = RedBlueCatchScene(_ManagerStub())
        scene._start_game()
        self.assertGreaterEqual(len(scene.round_data["balls"]), 2)

    def test_glasses_mode_uses_expected_speed_profile(self):
        board_service = RedBlueCatchScene(_ManagerStub()).board_service
        with patch("random.uniform", return_value=9.0):
            glasses_ball = board_service.create_ball(pygame.Rect(70, 136, 760, 462), stage_index=1, mode="glasses")
        self.assertEqual(glasses_ball["speed"], 6.0)

    def test_missed_ball_counts_failure(self):
        manager = _ManagerStub()
        scene = RedBlueCatchScene(manager)
        scene._start_game()
        ball = scene.round_data["balls"][0]
        ball["x"] = scene.play_area.left
        ball["y"] = scene.play_area.bottom - 28
        scene.update()
        self.assertEqual(scene.scoring.failure_count, 1)
        self.assertEqual(manager.sound_manager.wrong_calls, 1)

    def test_filter_direction_swaps_ball_eye_layer(self):
        scene = RedBlueCatchScene(_ManagerStub())
        scene.filter_direction = "left_red_right_blue"
        self.assertEqual(scene._layer_for_color("red"), "left")
        self.assertEqual(scene._layer_for_color("blue"), "right")
        scene.filter_direction = "left_blue_right_red"
        self.assertEqual(scene._layer_for_color("red"), "right")
        self.assertEqual(scene._layer_for_color("blue"), "left")

    def test_glasses_mode_draws_without_fullscreen_compositor(self):
        scene = RedBlueCatchScene(_ManagerStub())
        scene.mode = scene.MODE_GLASSES
        scene._start_game()
        surface = pygame.Surface((scene.width, scene.height))
        scene.draw(surface)
        self.assertEqual(scene.state, scene.STATE_PLAY)

    def test_session_finish_saves_result(self):
        manager = _ManagerStub()
        scene = RedBlueCatchScene(manager)
        scene._start_game()
        scene.session.session_started_at = time.time() - scene._session_seconds()
        scene.update()
        self.assertEqual(scene.state, scene.STATE_RESULT)
        self.assertEqual(manager.data_manager.saved[-1]["game_id"], "suppression.red_blue_catch")
        self.assertEqual(manager.sound_manager.completed_calls, 1)
