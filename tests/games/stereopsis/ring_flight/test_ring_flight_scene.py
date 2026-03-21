import os
import time
import unittest
from unittest.mock import patch

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")

import pygame

from games.stereopsis.ring_flight.scenes.root_scene import RingFlightScene


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
        self.frame_scale = 1.0

    def t(self, key, **kwargs):
        if kwargs:
            try:
                return key.format(**kwargs)
            except Exception:
                return key
        return key

    def set_scene(self, name):
        self.last_scene = name


class RingFlightSceneTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        pygame.init()

    @classmethod
    def tearDownClass(cls):
        pygame.quit()

    def test_glasses_filter_picker_can_start_session(self):
        manager = _ManagerStub()
        scene = RingFlightScene(manager)
        scene.show_filter_picker = True
        with patch("pygame.mouse.get_pos", return_value=scene.filter_start.center):
            scene.handle_events([pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=scene.filter_start.center)])
        self.assertEqual(scene.state, scene.STATE_PLAY)

    def test_successful_pass_scores_and_keeps_running(self):
        manager = _ManagerStub()
        scene = RingFlightScene(manager)
        scene._start_game()
        scene.target_depth_index = 0
        scene.wave = {
            "rings": [
                {"depth": 0, "x": float(scene.play_area.centerx), "progress": 1.0, "base_radius": 22, "target_radius": 68, "thickness": 16, "disparity": 28},
                {"depth": 1, "x": float(scene.play_area.left + 120), "progress": 1.0, "base_radius": 22, "target_radius": 68, "thickness": 16, "disparity": 18},
                {"depth": 2, "x": float(scene.play_area.right - 120), "progress": 1.0, "base_radius": 22, "target_radius": 68, "thickness": 16, "disparity": 10},
            ]
        }
        scene.plane_x = scene.play_area.centerx
        scene._finalize_wave_result(scene._classify_wave_selection()["result"])
        self.assertEqual(scene.scoring.success_count, 1)
        self.assertGreater(scene.scoring.score, 0)
        self.assertEqual(manager.sound_manager.correct_calls, 1)
        self.assertEqual(scene.state, scene.STATE_PLAY)

    def test_wrong_depth_counts_failure(self):
        manager = _ManagerStub()
        scene = RingFlightScene(manager)
        scene._start_game()
        scene.target_depth_index = 0
        scene.wave = {
            "rings": [
                {"depth": 0, "x": float(scene.play_area.left + 120), "progress": 1.0, "base_radius": 22, "target_radius": 68, "thickness": 16, "disparity": 28},
                {"depth": 1, "x": float(scene.play_area.centerx), "progress": 1.0, "base_radius": 22, "target_radius": 68, "thickness": 16, "disparity": 18},
                {"depth": 2, "x": float(scene.play_area.right - 120), "progress": 1.0, "base_radius": 22, "target_radius": 68, "thickness": 16, "disparity": 10},
            ]
        }
        scene.plane_x = scene.play_area.centerx
        scene._finalize_wave_result(scene._classify_wave_selection()["result"])
        self.assertEqual(scene.scoring.failure_count, 1)
        self.assertEqual(scene.scoring.wrong_depth_count, 1)
        self.assertEqual(manager.sound_manager.wrong_calls, 1)

    def test_target_depth_switches_after_three_successes(self):
        scene = RingFlightScene(_ManagerStub())
        scene._start_game()
        scene.target_depth_index = 0
        for _ in range(3):
            scene.scoring.on_success()
            scene._advance_target_if_needed()
        self.assertEqual(scene._current_target_depth(), 1)
        self.assertEqual(scene.scoring.target_switch_count, 1)

    def test_rings_stop_at_selection_line_until_confirmed(self):
        scene = RingFlightScene(_ManagerStub())
        scene._start_game()
        for ring in scene.wave["rings"]:
            ring["progress"] = scene.SELECT_PROGRESS - 0.002
        scene.update()
        self.assertTrue(scene.awaiting_selection)
        self.assertTrue(all(ring["progress"] == scene.SELECT_PROGRESS for ring in scene.wave["rings"]))

    def test_confirm_key_resolves_paused_wave(self):
        manager = _ManagerStub()
        scene = RingFlightScene(manager)
        scene._start_game()
        scene.awaiting_selection = True
        scene.target_depth_index = 0
        scene.wave = {
            "rings": [
                {"depth": 0, "x": float(scene.play_area.centerx), "progress": scene.SELECT_PROGRESS, "base_radius": 22, "target_radius": 68, "thickness": 16, "disparity": 28},
                {"depth": 1, "x": float(scene.play_area.left + 120), "progress": scene.SELECT_PROGRESS, "base_radius": 22, "target_radius": 68, "thickness": 16, "disparity": 18},
                {"depth": 2, "x": float(scene.play_area.right - 120), "progress": scene.SELECT_PROGRESS, "base_radius": 22, "target_radius": 68, "thickness": 16, "disparity": 10},
            ]
        }
        scene.plane_x = scene.play_area.centerx
        scene.handle_events([pygame.event.Event(pygame.KEYDOWN, key=pygame.K_SPACE)])
        self.assertIsNotNone(scene.fly_through)
        with patch("time.time", return_value=scene.fly_through["started_at"] + scene.fly_through["duration"] + 0.01):
            scene.update()
        self.assertEqual(scene.scoring.success_count, 1)
        self.assertFalse(scene.awaiting_selection)
        self.assertIsNone(scene.fly_through)

    def test_wrong_selection_keeps_same_rings_for_retry(self):
        manager = _ManagerStub()
        scene = RingFlightScene(manager)
        scene._start_game()
        scene.awaiting_selection = True
        scene.target_depth_index = 0
        original_wave = {
            "rings": [
                {"depth": 0, "x": float(scene.play_area.left + 120), "progress": scene.SELECT_PROGRESS, "base_radius": 22, "target_radius": 68, "thickness": 16, "disparity": 28},
                {"depth": 1, "x": float(scene.play_area.centerx), "progress": scene.SELECT_PROGRESS, "base_radius": 22, "target_radius": 68, "thickness": 16, "disparity": 18},
                {"depth": 2, "x": float(scene.play_area.right - 120), "progress": scene.SELECT_PROGRESS, "base_radius": 22, "target_radius": 68, "thickness": 16, "disparity": 10},
            ]
        }
        scene.wave = original_wave
        scene.plane_x = scene.play_area.centerx
        scene.handle_events([pygame.event.Event(pygame.KEYDOWN, key=pygame.K_SPACE)])
        self.assertIsNotNone(scene.fly_through)
        with patch("time.time", return_value=scene.fly_through["started_at"] + scene.fly_through["duration"] + 0.01):
            scene.update()
        self.assertEqual(scene.scoring.failure_count, 1)
        self.assertTrue(scene.awaiting_selection)
        self.assertIs(scene.wave, original_wave)

    def test_finish_saves_result(self):
        manager = _ManagerStub()
        scene = RingFlightScene(manager)
        scene._start_game()
        scene.scoring.success_count = 4
        scene.scoring.failure_count = 2
        scene.scoring.score = 90
        scene.session.session_started_at = time.time() - scene._session_seconds()
        scene.update()
        self.assertEqual(scene.state, scene.STATE_RESULT)
        self.assertEqual(manager.data_manager.saved[-1]["game_id"], "stereopsis.ring_flight")
        self.assertEqual(manager.sound_manager.completed_calls, 1)

    def test_frame_scale_keeps_forward_motion_consistent(self):
        manager = _ManagerStub()
        manager.frame_scale = 2.0
        scene = RingFlightScene(manager)
        scene._start_game()
        initial = scene.wave["rings"][0]["progress"]
        scene.update()
        self.assertAlmostEqual(scene.wave["rings"][0]["progress"], initial + scene.RING_SPEED * 2.0)

    def test_play_scene_renders_after_resize(self):
        scene = RingFlightScene(_ManagerStub())
        scene._start_game()
        scene.on_resize(840, 640)
        surface = pygame.Surface((840, 640))
        scene.draw(surface)
        self.assertGreater(sum(surface.get_at((420, 320))[:3]), 0)
