import os
import unittest
from unittest.mock import patch

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")

import pygame

from games.simultaneous.spot_difference.scenes.root_scene import SpotDifferenceScene
from games.simultaneous.spot_difference.services import SpotDifferenceBoardService


class _DataManagerStub:
    def __init__(self):
        self.saved = []

    def save_training_session(self, payload):
        self.saved.append(payload)
        return True


class _ManagerStub:
    def __init__(self):
        self.settings = {"language": "en-US", "session_duration_minutes": 5}
        self.active_game_id = "simultaneous.spot_difference"
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


class SpotDifferenceSceneTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        pygame.init()

    @classmethod
    def tearDownClass(cls):
        pygame.quit()

    def test_glasses_mode_can_start_and_finish(self):
        manager = _ManagerStub()
        scene = SpotDifferenceScene(manager)
        scene.show_filter_picker = True
        with patch("pygame.mouse.get_pos", return_value=scene.filter_start.center):
            scene.handle_events([pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=scene.filter_start.center)])
        self.assertEqual(scene.state, scene.STATE_PLAY)
        scene.selected_index = scene.round_data["diff_index"]
        scene.handle_events([pygame.event.Event(pygame.KEYDOWN, key=pygame.K_SPACE)])
        scene.session.session_started_at = __import__("time").time() - scene._session_seconds()
        scene.update()
        self.assertEqual(scene.state, scene.STATE_RESULT)
        self.assertEqual(manager.data_manager.saved[-1]["game_id"], "simultaneous.spot_difference")

    def test_keyboard_selection_can_move_and_confirm(self):
        manager = _ManagerStub()
        scene = SpotDifferenceScene(manager)
        scene._start_game()
        scene.selected_index = 0
        scene.handle_events([pygame.event.Event(pygame.KEYDOWN, key=pygame.K_RIGHT)])
        self.assertEqual(scene.selected_index, 1)
        first_index = scene.round_data["diff_indices"][0]
        scene.selected_index = first_index
        scene.handle_events([pygame.event.Event(pygame.KEYDOWN, key=pygame.K_SPACE)])
        self.assertIn(first_index, scene.pending_indices)
        scene.handle_events([pygame.event.Event(pygame.KEYDOWN, key=pygame.K_RETURN)])
        self.assertGreaterEqual(scene.scoring.success_count, 1)
        self.assertNotIn(first_index, scene.pending_indices)

    def test_multiple_marked_differences_submit_once(self):
        manager = _ManagerStub()
        scene = SpotDifferenceScene(manager)
        scene._start_game()
        targets = scene.round_data["diff_indices"][:2]
        for index in targets:
            scene.selected_index = index
            scene.handle_events([pygame.event.Event(pygame.KEYDOWN, key=pygame.K_SPACE)])
        self.assertEqual(set(targets), scene.pending_indices)
        before = scene.scoring.success_count
        scene.handle_events([pygame.event.Event(pygame.KEYDOWN, key=pygame.K_RETURN)])
        self.assertGreaterEqual(scene.scoring.success_count, before + len(targets))

    def test_mouse_click_same_shape_toggles_pending_selection(self):
        manager = _ManagerStub()
        scene = SpotDifferenceScene(manager)
        scene._start_game()
        target = scene.round_data["diff_indices"][0]
        item = scene.round_data["right"][target]
        pos = (scene.right_panel.x + item["center"][0], scene.right_panel.y + item["center"][1])
        with patch("pygame.mouse.get_pos", return_value=pos):
            scene.handle_events([pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=pos)])
            self.assertIn(target, scene.pending_indices)
            scene.handle_events([pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=pos)])
            self.assertNotIn(target, scene.pending_indices)
            self.assertEqual(scene.selected_index, -1)

    def test_board_service_generates_local_centers_and_multiple_differences(self):
        service = SpotDifferenceBoardService()
        self.assertGreaterEqual(len(service.SHAPES), 6)
        board = pygame.Rect(84, 148, 300, 260)
        round_data = service.create_round(board, diff_count=4)
        self.assertEqual(len(round_data["diff_indices"]), 4)
        self.assertEqual(len(round_data["diff_details"]), 4)
        for item in round_data["left"]:
            self.assertGreaterEqual(item["center"][0], 0)
            self.assertLessEqual(item["center"][0], board.width)
            self.assertGreaterEqual(item["center"][1], 0)
            self.assertLessEqual(item["center"][1], board.height)
        size_details = [detail for detail in round_data["diff_details"] if detail["type"] == service.DIFF_SIZE]
        for detail in size_details:
            left_size = round_data["left"][detail["index"]]["size"]
            right_size = round_data["right"][detail["index"]]["size"]
            self.assertGreaterEqual(abs(left_size - right_size), 14)

    def test_board_service_can_draw_extended_shapes(self):
        service = SpotDifferenceBoardService()
        surface = pygame.Surface((120, 120), pygame.SRCALPHA)
        for shape in service.SHAPES:
            service.draw_shape(surface, shape, (60, 60), 36, (255, 120, 90))
        bounds = surface.get_bounding_rect()
        self.assertGreater(bounds.width, 0)
        self.assertGreater(bounds.height, 0)

    def test_round_clear_waits_for_flash_then_refreshes(self):
        manager = _ManagerStub()
        scene = SpotDifferenceScene(manager)
        scene._start_game()
        diff_indices = list(scene.round_data["diff_indices"])
        original_round = scene.round_data
        for index in diff_indices:
            scene.selected_index = index
            scene._confirm_selection()
        self.assertGreater(scene.round_flash_until, 0.0)
        self.assertIs(scene.round_data, original_round)
        scene.feedback_until = 0.0
        scene.round_flash_until = __import__("time").time() - 0.1
        scene.update()
        self.assertIsNot(scene.round_data, original_round)


if __name__ == "__main__":
    unittest.main()
