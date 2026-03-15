import os
import unittest
from unittest.mock import patch

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")

import pygame

from games.suppression.find_same.scenes.root_scene import FindSameScene
from games.suppression.find_same.services import FindSameBoardService


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
        self.active_game_id = "suppression.find_same"
        self.active_category = "suppression"
        self.last_scene = None
        self.data_manager = _DataManagerStub()
        self.sound_manager = _SoundManagerStub()

    def t(self, key, **kwargs):
        if kwargs:
            try:
                return key.format(**kwargs)
            except Exception:
                return key
        return key

    def set_scene(self, name):
        self.last_scene = name


class FindSameSceneTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        pygame.init()

    @classmethod
    def tearDownClass(cls):
        pygame.quit()

    def test_glasses_mode_can_start_and_finish(self):
        manager = _ManagerStub()
        scene = FindSameScene(manager)
        scene.show_filter_picker = True
        with patch("pygame.mouse.get_pos", return_value=scene.filter_start.center):
            scene.handle_events([pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=scene.filter_start.center)])
        self.assertEqual(scene.state, scene.STATE_PLAY)
        scene.pending_indices = set(scene.round_data["match_indices"])
        scene._confirm_selection()
        scene.session.session_started_at = __import__("time").time() - scene._session_seconds()
        scene.update()
        self.assertEqual(scene.state, scene.STATE_RESULT)
        self.assertEqual(manager.data_manager.saved[-1]["game_id"], "suppression.find_same")
        self.assertEqual(manager.sound_manager.correct_calls, 1)
        self.assertEqual(manager.sound_manager.completed_calls, 1)

    def test_keyboard_selection_can_move_and_confirm(self):
        manager = _ManagerStub()
        scene = FindSameScene(manager)
        scene._start_game()
        scene.selected_index = 0
        scene.handle_events([pygame.event.Event(pygame.KEYDOWN, key=pygame.K_RIGHT)])
        self.assertEqual(scene.selected_index, 1)
        scene.pending_indices = set(scene.round_data["match_indices"])
        before = scene.scoring.success_count
        scene._confirm_selection()
        self.assertGreater(scene.scoring.success_count, before)

    def test_wrong_selection_counts_failure(self):
        manager = _ManagerStub()
        scene = FindSameScene(manager)
        scene._start_game()
        wrong_index = next(index for index in range(len(scene.round_data["right"])) if index not in scene.round_data["match_indices"])
        scene.pending_indices = {wrong_index}
        scene._confirm_selection()
        self.assertEqual(scene.failure_count, 1)
        self.assertEqual(manager.sound_manager.wrong_calls, 1)

    def test_glasses_filter_direction_changes_render(self):
        scene = FindSameScene(_ManagerStub())
        scene._start_game()
        scene.mode = scene.MODE_GLASSES
        first = pygame.Surface((scene.width, scene.height), pygame.SRCALPHA)
        second = pygame.Surface((scene.width, scene.height), pygame.SRCALPHA)
        scene.filter_direction = "left_red_right_blue"
        scene.draw(first)
        scene.filter_direction = "left_blue_right_red"
        scene.draw(second)
        self.assertNotEqual(pygame.image.tostring(first, "RGBA"), pygame.image.tostring(second, "RGBA"))

    def test_filter_picker_can_draw_without_crashing(self):
        scene = FindSameScene(_ManagerStub())
        scene.show_filter_picker = True
        surface = pygame.Surface((scene.width, scene.height), pygame.SRCALPHA)
        scene.draw(surface)

    def test_play_draws_vertical_dashed_divider_between_panels(self):
        scene = FindSameScene(_ManagerStub())
        scene._start_game()
        surface = pygame.Surface((scene.width, scene.height), pygame.SRCALPHA)
        scene.draw(surface)
        divider_x = scene.left_panel.right + (scene.right_panel.left - scene.left_panel.right) // 2
        dash_y = scene.left_panel.y + 12
        self.assertEqual(surface.get_at((divider_x, dash_y))[:3], (196, 210, 230))

    def test_mouse_click_shape_toggles_pending_selection(self):
        manager = _ManagerStub()
        scene = FindSameScene(manager)
        scene._start_game()
        target = scene.round_data["match_indices"][0]
        item = scene.round_data["right"][target]
        pos = (scene.right_panel.x + item["center"][0], scene.right_panel.y + item["center"][1])
        with patch("pygame.mouse.get_pos", return_value=pos):
            scene.handle_events([pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=pos)])
            self.assertIn(target, scene.pending_indices)
            scene.handle_events([pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=pos)])
            self.assertNotIn(target, scene.pending_indices)

    def test_board_service_generates_matches_and_decoys(self):
        service = FindSameBoardService()
        board = pygame.Rect(84, 148, 300, 260)
        round_data = service.create_round(board, match_count=4)
        self.assertEqual(len(round_data["left"]), 4)
        self.assertEqual(len(round_data["match_indices"]), 4)
        for ref_index, target_index in enumerate(round_data["match_indices"]):
            left = round_data["left"][ref_index]
            right = round_data["right"][target_index]
            self.assertEqual((left["shape"], left["color"], left["size"]), (right["shape"], right["color"], right["size"]))


if __name__ == "__main__":
    unittest.main()
