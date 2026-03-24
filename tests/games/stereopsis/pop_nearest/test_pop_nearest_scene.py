import os
import time
import unittest
from unittest.mock import patch

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")

import pygame

from games.stereopsis.pop_nearest.scenes.root_scene import PopNearestScene


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


class PopNearestSceneTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        pygame.init()

    @classmethod
    def tearDownClass(cls):
        pygame.quit()

    def test_filter_picker_can_start_session(self):
        scene = PopNearestScene(_ManagerStub())
        scene.show_filter_picker = True
        with patch("pygame.mouse.get_pos", return_value=scene.filter_start.center):
            scene.handle_events([pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=scene.filter_start.center)])
        self.assertEqual(scene.state, scene.STATE_PLAY)
        self.assertEqual(scene.session.completed_groups, 0)

    def test_correct_click_pops_nearest_balloon(self):
        manager = _ManagerStub()
        scene = PopNearestScene(manager)
        scene._start_game()
        nearest_index = next(i for i, b in enumerate(scene.group_data["balloons"]) if b["depth_rank"] == 0)
        target = scene._balloon_display_state(scene.group_data["balloons"][nearest_index])["center"]
        scene.handle_events([pygame.event.Event(pygame.MOUSEMOTION, pos=target, rel=(0, 0), buttons=(0, 0, 0))])
        scene.handle_events([pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=(target[0], scene.play_area.bottom - 12))])
        self.assertIsNotNone(scene.active_shot)
        with patch("time.time", return_value=scene.active_shot["started_at"] + scene.active_shot["duration"] + 0.01):
            scene.update()
        self.assertTrue(scene.group_data["balloons"][nearest_index]["popped"])
        self.assertEqual(manager.sound_manager.correct_calls, 1)

    def test_wrong_click_does_not_remove_balloon(self):
        manager = _ManagerStub()
        scene = PopNearestScene(manager)
        scene._start_game()
        wrong_index = next(i for i, b in enumerate(scene.group_data["balloons"]) if b["depth_rank"] == 3)
        nearest_index = next(i for i, b in enumerate(scene.group_data["balloons"]) if b["depth_rank"] == 0)
        scene.group_data["balloons"][nearest_index]["base_center"] = (scene.play_area.left + 100, scene.group_data["balloons"][nearest_index]["base_center"][1])
        scene.group_data["balloons"][wrong_index]["base_center"] = (scene.play_area.right - 100, scene.group_data["balloons"][wrong_index]["base_center"][1])
        target = scene._balloon_display_state(scene.group_data["balloons"][wrong_index])["center"]
        scene.handle_events([pygame.event.Event(pygame.MOUSEMOTION, pos=target, rel=(0, 0), buttons=(0, 0, 0))])
        scene.handle_events([pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=(target[0], scene.play_area.bottom - 12))])
        self.assertIsNotNone(scene.active_shot)
        with patch("time.time", return_value=scene.active_shot["started_at"] + scene.active_shot["duration"] + 0.01):
            scene.update()
        self.assertFalse(scene.group_data["balloons"][wrong_index]["popped"])
        self.assertEqual(scene.scoring.wrong_pops, 1)
        self.assertEqual(manager.sound_manager.wrong_calls, 1)

    def test_group_balloons_keep_same_radius(self):
        scene = PopNearestScene(_ManagerStub())
        scene._start_game()
        radii = {balloon["radius"] for balloon in scene.group_data["balloons"]}
        self.assertEqual(radii, {42})
        self.assertEqual(len(scene.group_data["balloons"]), 4)

    def test_group_layout_keeps_clear_vertical_spacing(self):
        scene = PopNearestScene(_ManagerStub())
        scene._start_game()
        positions = sorted((balloon["base_center"][1] for balloon in scene.group_data["balloons"]))
        gaps = [positions[idx + 1] - positions[idx] for idx in range(len(positions) - 1)]
        self.assertTrue(all(gap >= 55 for gap in gaps))

    def test_last_balloon_waits_for_impact_before_next_group(self):
        manager = _ManagerStub()
        scene = PopNearestScene(manager)
        scene._start_game()
        current_group = scene.group_data
        for balloon in scene.group_data["balloons"]:
            balloon["popped"] = balloon["depth_rank"] != 0
        nearest_index = next(i for i, b in enumerate(scene.group_data["balloons"]) if b["depth_rank"] == 0)
        target = scene._balloon_display_state(scene.group_data["balloons"][nearest_index])["center"]
        scene.handle_events([pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=(target[0], scene.play_area.bottom - 12))])
        with patch("time.time", return_value=scene.active_shot["started_at"] + scene.active_shot["duration"] + 0.01):
            scene.update()
        self.assertIs(scene.group_data, current_group)
        self.assertTrue(scene.pending_group_advance)
        with patch("time.time", return_value=scene.impact_effect["started_at"] + scene.impact_effect["duration"] + 0.01):
            scene.update()
        self.assertIsNot(scene.group_data, current_group)

    def test_keyboard_move_and_fire_work(self):
        manager = _ManagerStub()
        scene = PopNearestScene(manager)
        scene._start_game()
        initial = scene.bow_x
        scene.handle_events([pygame.event.Event(pygame.KEYDOWN, key=pygame.K_RIGHT)])
        self.assertGreater(scene.bow_x, initial)
        scene.handle_events([pygame.event.Event(pygame.KEYDOWN, key=pygame.K_SPACE)])
        self.assertIsNotNone(scene.active_shot)
        self.assertEqual(scene.active_shot["shot_x"], scene.bow_x)

    def test_mouse_move_updates_bow_linearly(self):
        scene = PopNearestScene(_ManagerStub())
        scene._start_game()
        scene.handle_events([pygame.event.Event(pygame.MOUSEMOTION, pos=(scene.play_area.left + 40, scene.play_area.bottom), rel=(0, 0), buttons=(0, 0, 0))])
        left_x = scene.bow_x
        scene.handle_events([pygame.event.Event(pygame.MOUSEMOTION, pos=(scene.play_area.right - 40, scene.play_area.bottom), rel=(0, 0), buttons=(0, 0, 0))])
        right_x = scene.bow_x
        self.assertLess(left_x, right_x)

    def test_mouse_click_uses_vertical_shot(self):
        manager = _ManagerStub()
        scene = PopNearestScene(manager)
        scene._start_game()
        nearest_index = next(i for i, b in enumerate(scene.group_data["balloons"]) if b["depth_rank"] == 0)
        target = scene._balloon_display_state(scene.group_data["balloons"][nearest_index])["center"]
        click_pos = (target[0], scene.play_area.bottom - 16)
        scene.handle_events([pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=click_pos)])
        self.assertIsNotNone(scene.active_shot)
        self.assertEqual(scene.bow_x, click_pos[0])
        self.assertEqual(scene.active_shot["shot_x"], click_pos[0])
        self.assertEqual(scene.active_shot["target_y"], target[1])

    def test_click_without_balloon_lane_still_fires_arrow(self):
        manager = _ManagerStub()
        scene = PopNearestScene(manager)
        scene._start_game()
        scene.handle_events([pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=(scene.play_area.left + 8, scene.play_area.bottom - 16))])
        self.assertIsNotNone(scene.active_shot)
        self.assertTrue(scene.active_shot["miss"])

    def test_group_timeout_starts_new_group(self):
        manager = _ManagerStub()
        scene = PopNearestScene(manager)
        scene._start_game()
        first_group = scene.group_data
        scene.session.group_started_at = time.time() - scene.session.group_seconds
        scene.update()
        self.assertIsNot(scene.group_data, first_group)
        self.assertEqual(manager.sound_manager.wrong_calls, 1)

    def test_finish_saves_result(self):
        manager = _ManagerStub()
        scene = PopNearestScene(manager)
        scene._start_game()
        scene.scoring.correct_pops = 4
        scene.scoring.wrong_pops = 1
        scene.scoring.score = 58
        scene.scoring.groups_cleared = 2
        scene.scoring.best_streak = 3
        scene.scoring.total_pop_time = 4.0
        scene.session.session_elapsed = 80
        scene._finish_game()
        self.assertEqual(scene.state, scene.STATE_RESULT)
        self.assertEqual(manager.data_manager.saved[-1]["game_id"], "stereopsis.pop_nearest")
        self.assertEqual(manager.sound_manager.completed_calls, 1)

    def test_play_scene_renders_after_resize(self):
        scene = PopNearestScene(_ManagerStub())
        scene._start_game()
        scene.on_resize(840, 640)
        surface = pygame.Surface((840, 640))
        scene.draw(surface)
        total = 0
        for x in range(320, 521, 40):
            for y in range(180, 381, 40):
                total += sum(surface.get_at((x, y))[:3])
        self.assertGreater(total, 0)
