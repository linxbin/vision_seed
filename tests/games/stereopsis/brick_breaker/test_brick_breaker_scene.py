import os
import time
import unittest
from unittest.mock import patch

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")

import pygame

from games.stereopsis.brick_breaker.scenes.root_scene import BrickBreakerScene


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


class BrickBreakerSceneTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        pygame.init()

    @classmethod
    def tearDownClass(cls):
        pygame.quit()

    def test_glasses_mode_can_start(self):
        scene = BrickBreakerScene(_ManagerStub())
        scene.show_filter_picker = True
        with patch("pygame.mouse.get_pos", return_value=scene.filter_start.center):
            scene.handle_events([pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=scene.filter_start.center)])
        self.assertEqual(scene.state, scene.STATE_PLAY)

    def test_reset_returns_to_home_and_clears_glasses_state(self):
        scene = BrickBreakerScene(_ManagerStub())
        scene.mode = scene.MODE_GLASSES
        scene.state = scene.STATE_PLAY
        scene.show_filter_picker = True
        scene.reset()
        self.assertEqual(scene.state, scene.STATE_HOME)
        self.assertEqual(scene.mode, scene.MODE_NAKED)
        self.assertFalse(scene.show_filter_picker)

    def test_round_has_single_row_with_random_depths(self):
        scene = BrickBreakerScene(_ManagerStub())
        scene._start_game()
        ys = {brick["rect"][1] for brick in scene.round_data["bricks"]}
        depths = {brick["depth"] for brick in scene.round_data["bricks"]}
        self.assertEqual(len(ys), 1)
        self.assertTrue(depths.issubset({0, 1, 2}))
        self.assertIn(scene.round_data["attack_depth"], depths)

    def test_click_launches_attack_ball(self):
        scene = BrickBreakerScene(_ManagerStub())
        scene._start_game()
        pos = (scene.play_area.centerx, scene.play_area.bottom - 40)
        scene.handle_events([pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=pos)])
        self.assertIsNotNone(scene.round_data["attack_ball"])
        self.assertEqual(scene.scoring.shot_count, 1)

    def test_matching_depth_brick_is_removed(self):
        manager = _ManagerStub()
        scene = BrickBreakerScene(manager)
        scene._start_game()
        scene.round_data["bricks"] = [
            {"rect": [120, 180, 92, 34], "depth": 1},
            {"rect": [224, 180, 92, 34], "depth": 1},
            {"rect": [328, 180, 92, 34], "depth": 2},
        ]
        scene.round_data["attack_depth"] = 1
        brick = scene.round_data["bricks"][0]
        scene.round_data["attack_ball"] = {
            "x": brick["rect"][0] + brick["rect"][2] // 2,
            "y": brick["rect"][1] + brick["rect"][3] // 2,
            "radius": 13,
            "speed": 11,
            "depth": 1,
        }
        before = len(scene.round_data["bricks"])
        scene.update()
        self.assertEqual(len(scene.round_data["bricks"]), before - 1)
        self.assertEqual(scene.scoring.target_hits, 1)
        self.assertEqual(manager.sound_manager.correct_calls, 1)

    def test_wrong_depth_brick_triggers_failure_feedback(self):
        manager = _ManagerStub()
        scene = BrickBreakerScene(manager)
        scene._start_game()
        target_depth = scene.round_data["attack_depth"]
        wrong_brick = next(item for item in scene.round_data["bricks"] if item["depth"] != target_depth)
        scene.round_data["attack_ball"] = {
            "x": wrong_brick["rect"][0] + wrong_brick["rect"][2] // 2,
            "y": wrong_brick["rect"][1] + wrong_brick["rect"][3] // 2,
            "radius": 13,
            "speed": 11,
            "depth": target_depth,
        }
        before = len(scene.round_data["bricks"])
        scene.update()
        self.assertEqual(len(scene.round_data["bricks"]), before)
        self.assertEqual(scene.scoring.depth_confusion, 1)
        self.assertIsNone(scene.round_data["attack_ball"])
        self.assertEqual(manager.sound_manager.wrong_calls, 1)

    def test_clearing_last_matching_depth_refreshes_row_and_attack_depth(self):
        manager = _ManagerStub()
        scene = BrickBreakerScene(manager)
        scene._start_game()
        scene.round_data["bricks"] = [
            {"rect": [120, 180, 92, 34], "depth": 1},
            {"rect": [224, 180, 92, 34], "depth": 2},
        ]
        scene.round_data["attack_depth"] = 1
        scene.round_data["attack_ball"] = {
            "x": 166,
            "y": 197,
            "radius": 13,
            "speed": 11,
            "depth": 1,
        }
        scene.update()
        self.assertEqual(scene.scoring.refresh_count, 1)
        self.assertIsNone(scene.round_data["attack_ball"])
        self.assertGreaterEqual(len(scene.round_data["bricks"]), 1)
        self.assertIn(scene.round_data["attack_depth"], {brick["depth"] for brick in scene.round_data["bricks"]})

    def test_glasses_filter_direction_changes_render(self):
        scene = BrickBreakerScene(_ManagerStub())
        scene._start_game()
        scene.mode = scene.MODE_GLASSES
        first = pygame.Surface((scene.width, scene.height), pygame.SRCALPHA)
        second = pygame.Surface((scene.width, scene.height), pygame.SRCALPHA)
        scene.filter_direction = "left_red_right_blue"
        scene.draw(first)
        scene.filter_direction = "left_blue_right_red"
        scene.draw(second)
        self.assertNotEqual(pygame.image.tostring(first, "RGBA"), pygame.image.tostring(second, "RGBA"))

    def test_glasses_mode_draws_visible_pink_play_background(self):
        scene = BrickBreakerScene(_ManagerStub())
        scene._start_game()
        scene.mode = scene.MODE_GLASSES
        surface = pygame.Surface((scene.width, scene.height), pygame.SRCALPHA)
        scene.draw(surface)
        sample = surface.get_at((scene.play_area.left + 20, scene.play_area.top + 24))[:3]
        self.assertEqual(sample, (255, 19, 255))

    def test_finish_saves_result(self):
        manager = _ManagerStub()
        scene = BrickBreakerScene(manager)
        scene._start_game()
        scene.session.session_started_at = time.time() - scene._session_seconds()
        scene.update()
        self.assertEqual(scene.state, scene.STATE_RESULT)
        self.assertEqual(manager.data_manager.saved[-1]["game_id"], "stereopsis.brick_breaker")
        self.assertEqual(manager.sound_manager.completed_calls, 1)
