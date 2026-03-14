import math
import os
import time
import unittest
from unittest.mock import patch

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")

import pygame

from games.stereopsis.depth_grab.scenes.root_scene import DepthGrabScene
from games.stereopsis.depth_grab.services.board_service import DepthGrabBoardService


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


class DepthGrabSceneTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        pygame.init()

    @classmethod
    def tearDownClass(cls):
        pygame.quit()

    def test_glasses_filter_picker_can_start_session(self):
        manager = _ManagerStub()
        scene = DepthGrabScene(manager)
        scene.show_filter_picker = True
        with patch("pygame.mouse.get_pos", return_value=scene.filter_start.center):
            scene.handle_events([pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=scene.filter_start.center)])
        self.assertEqual(scene.state, scene.STATE_PLAY)

    def test_correct_click_scores(self):
        manager = _ManagerStub()
        scene = DepthGrabScene(manager)
        scene._start_game()
        scene.round_data = {
            "targets": [
                {"center": (120, 120), "radius": 30, "depth_rank": 1, "disparity": 10, "sparkle_count": 2},
                {"center": (200, 120), "radius": 36, "depth_rank": 0, "disparity": 18, "sparkle_count": 4},
            ],
            "correct_index": 1,
            "stage_index": 1,
        }
        scene.session.round_started_at = time.time() - 1.3
        scene.session.tick(time.time())
        scene._resolve_click((200, 120))
        self.assertEqual(scene.scoring.success_count, 1)
        self.assertGreater(scene.scoring.score, 0)
        self.assertEqual(manager.sound_manager.correct_calls, 1)

    def test_wrong_click_counts_confusion(self):
        manager = _ManagerStub()
        scene = DepthGrabScene(manager)
        scene._start_game()
        scene.round_data = {
            "targets": [
                {"center": (120, 120), "radius": 30, "depth_rank": 2, "disparity": 6, "sparkle_count": 2},
                {"center": (200, 120), "radius": 36, "depth_rank": 0, "disparity": 18, "sparkle_count": 4},
            ],
            "correct_index": 1,
            "stage_index": 2,
        }
        scene._resolve_click((120, 120))
        self.assertEqual(scene.scoring.failure_count, 1)
        self.assertEqual(scene.scoring.front_back_confusion_count, 1)
        self.assertEqual(manager.sound_manager.wrong_calls, 1)

    def test_click_inside_circle_but_outside_star_does_not_hit(self):
        scene = DepthGrabScene(_ManagerStub())
        scene._start_game()
        center = (220, 180)
        radius = 40
        variant = {"tips": 5, "rotation": -1.57}
        scene.round_data = {
            "targets": [
                {
                    "center": center,
                    "radius": radius,
                    "depth_rank": 0,
                    "disparity": 18,
                    "layer_offset": 0,
                    "star_variant": variant,
                    "naked_color": (255, 129, 146),
                }
            ],
            "correct_index": 0,
            "stage_index": 0,
        }
        miss_point = None
        for ratio in (0.82, 0.78, 0.74, 0.7, 0.66, 0.62):
            for step in range(36):
                angle = math.tau * step / 36
                candidate = (
                    center[0] + math.cos(angle) * radius * ratio,
                    center[1] + math.sin(angle) * radius * ratio,
                )
                if not scene._point_in_star(candidate, center, radius, variant):
                    miss_point = candidate
                    break
            if miss_point is not None:
                break
        self.assertIsNotNone(miss_point)
        self.assertIsNone(scene._target_hit(miss_point))

    def test_glasses_mode_clicking_either_color_block_counts_as_hit(self):
        scene = DepthGrabScene(_ManagerStub())
        scene.mode = scene.MODE_GLASSES
        center = (260, 210)
        radius = 34
        disparity = 20
        variant = {"tips": 5, "rotation": -1.57}
        scene.round_data = {
            "targets": [
                {
                    "center": center,
                    "radius": radius,
                    "depth_rank": 0,
                    "disparity": disparity,
                    "layer_offset": 0,
                    "star_variant": variant,
                }
            ],
            "correct_index": 0,
            "stage_index": 0,
        }
        eye_shift = disparity // 2
        self.assertEqual(scene._target_hit((center[0] - eye_shift, center[1])), 0)
        self.assertEqual(scene._target_hit((center[0] + eye_shift, center[1])), 0)

    def test_clicking_display_center_after_animation_counts_as_hit(self):
        scene = DepthGrabScene(_ManagerStub())
        scene._start_game()
        scene._depth_phase = 1.35
        scene.round_data = {
            "targets": [
                {
                    "center": (240, 220),
                    "radius": 34,
                    "depth_rank": 0,
                    "disparity": 20,
                    "layer_offset": -12,
                    "star_variant": {"tips": 5, "rotation": -1.57},
                    "naked_color": (255, 129, 146),
                }
            ],
            "correct_index": 0,
            "stage_index": 0,
        }
        display = scene._target_display_state(scene.round_data["targets"][0], 0)
        self.assertEqual(scene._target_hit(display["center"]), 0)

    def test_finish_saves_result(self):
        manager = _ManagerStub()
        scene = DepthGrabScene(manager)
        scene._start_game()
        scene.scoring.success_count = 3
        scene.scoring.failure_count = 1
        scene.scoring.score = 88
        scene.session.session_started_at = time.time() - scene._session_seconds()
        scene.update()
        self.assertEqual(scene.state, scene.STATE_RESULT)
        self.assertEqual(manager.data_manager.saved[-1]["game_id"], "stereopsis.depth_grab")
        self.assertEqual(manager.sound_manager.completed_calls, 1)

    def test_round_uses_stronger_disparity_values(self):
        scene = DepthGrabScene(_ManagerStub())
        scene._start_game()
        disparities = [target["disparity"] for target in scene.round_data["targets"]]
        self.assertGreaterEqual(max(disparities), 28)
        self.assertGreaterEqual(max(disparities) - min(disparities), 14)

    def test_round_contains_more_stereo_targets(self):
        scene = DepthGrabScene(_ManagerStub())
        scene._start_game()
        self.assertGreaterEqual(len(scene.round_data["targets"]), 6)
        variants = [target["star_variant"] for target in scene.round_data["targets"]]
        self.assertTrue(all("tips" in variant and "rotation" in variant for variant in variants))
        self.assertTrue(all(variant["tips"] == 5 for variant in variants))
        colors = {target["naked_color"] for target in scene.round_data["targets"]}
        self.assertGreaterEqual(len(colors), 3)
        radii = {target["radius"] for target in scene.round_data["targets"]}
        self.assertEqual(radii, {32})

    def test_nearest_star_is_not_always_the_largest(self):
        service = DepthGrabBoardService()
        play_area = pygame.Rect(60, 128, 780, 450)
        round_data = service.create_round(play_area, 1)
        radii = {target["radius"] for target in round_data["targets"]}
        self.assertEqual(radii, {32})

    def test_correct_index_always_points_to_nearest_star(self):
        service = DepthGrabBoardService()
        play_area = pygame.Rect(60, 128, 780, 450)
        for _ in range(12):
            round_data = service.create_round(play_area, 1)
            correct = round_data["targets"][round_data["correct_index"]]
            self.assertEqual(correct["depth_rank"], 0)

    def test_round_targets_stay_inside_play_area_and_do_not_overlap(self):
        scene = DepthGrabScene(_ManagerStub())
        scene._start_game()
        targets = scene.round_data["targets"]
        display_states = [scene._target_display_state(target, idx) for idx, target in enumerate(targets)]
        for target, display in zip(targets, display_states):
            x, y = display["center"]
            radius = display["glasses_radius"]
            self.assertGreaterEqual(x - radius, scene.play_area.left)
            self.assertLessEqual(x + radius, scene.play_area.right)
            self.assertGreaterEqual(y - radius, scene.play_area.top)
            self.assertLessEqual(y + radius, scene.play_area.bottom)
        for idx, first_display in enumerate(display_states):
            for second_display in display_states[idx + 1 :]:
                distance = math.hypot(
                    first_display["center"][0] - second_display["center"][0],
                    first_display["center"][1] - second_display["center"][1],
                )
                self.assertGreaterEqual(distance, first_display["glasses_radius"] + second_display["glasses_radius"] + 12)
