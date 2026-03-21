import os
import unittest
from unittest.mock import patch

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")

import pygame

from games.fusion.push_box.scenes.root_scene import FusionPushBoxScene
from games.fusion.push_box.services.board_service import FusionPushBoxBoardService


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
        self.active_game_id = "fusion.push_box"
        self.active_category = "fusion"
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


class FusionPushBoxSceneTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        pygame.init()

    @classmethod
    def tearDownClass(cls):
        pygame.quit()

    def test_glasses_filter_picker_can_start_session(self):
        manager = _ManagerStub()
        scene = FusionPushBoxScene(manager)
        scene.show_filter_picker = True
        with patch("pygame.mouse.get_pos", return_value=scene.filter_start.center):
            scene.handle_events([pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=scene.filter_start.center)])
        self.assertEqual(scene.state, scene.STATE_PLAY)

    def test_pushing_box_to_target_clears_level(self):
        manager = _ManagerStub()
        scene = FusionPushBoxScene(manager)
        scene._start_game()
        scene.board_state = {
            "width": 5,
            "height": 5,
            "walls": {(0, 0)},
            "targets": {(3, 1)},
            "boxes": {(2, 1)},
            "player": (1, 1),
            "steps": 0,
            "pushes": 0,
            "level_index": 0,
        }
        scene._attempt_move("right")
        self.assertEqual(scene.scoring.clear_count, 1)
        self.assertEqual(scene.level_index, 1)

    def test_session_finish_saves_result(self):
        manager = _ManagerStub()
        scene = FusionPushBoxScene(manager)
        scene._start_game()
        scene.scoring.clear_count = 2
        scene.scoring.score = 260
        scene.scoring.total_steps = 14
        scene.scoring.total_pushes = 5
        scene.scoring.best_streak = 2
        scene.session.session_started_at = __import__("time").time() - scene._session_seconds()
        scene.update()
        self.assertEqual(scene.state, scene.STATE_RESULT)
        self.assertEqual(manager.data_manager.saved[-1]["game_id"], "fusion.push_box")

    def test_all_levels_are_solvable(self):
        board = FusionPushBoxBoardService()
        for level_index in range(len(board.LEVELS)):
            self.assertTrue(board.is_level_solvable(level_index), level_index)

    def test_deadlock_restarts_current_level(self):
        manager = _ManagerStub()
        scene = FusionPushBoxScene(manager)
        scene._start_game()
        scene.level_index = 0
        scene.board_state = {
            "width": 7,
            "height": 7,
            "walls": {
                (x, 0) for x in range(7)
            }
            | {(x, 6) for x in range(7)}
            | {(0, y) for y in range(7)}
            | {(6, y) for y in range(7)}
            | {(3, 1), (5, 1), (4, 2), (3, 4), (5, 4), (4, 3)},
            "targets": {(1, 1)},
            "boxes": {(4, 1), (4, 4)},
            "player": (2, 3),
            "steps": 0,
            "pushes": 0,
            "level_index": 0,
        }
        scene._attempt_move("left")
        self.assertGreater(scene.restart_pending_until, 0.0)
        with patch("time.time", return_value=scene.restart_pending_until + 0.01):
            scene.update()
        self.assertEqual(scene.board_state["player"], FusionPushBoxBoardService().create_level(0)["player"])
        self.assertEqual(manager.sound_manager.wrong_calls, 1)

    def test_unsolvable_corner_state_restarts_even_with_other_pushes_available(self):
        manager = _ManagerStub()
        scene = FusionPushBoxScene(manager)
        scene._start_game()
        scene.level_index = 0
        initial_player = FusionPushBoxBoardService().create_level(0)["player"]
        scene.board_state = {
            "width": 7,
            "height": 7,
            "walls": {
                (x, 0) for x in range(7)
            }
            | {(x, 6) for x in range(7)}
            | {(0, y) for y in range(7)}
            | {(6, y) for y in range(7)},
            "targets": {(4, 4), (5, 2)},
            "boxes": {(1, 1), (3, 3)},
            "player": (2, 3),
            "steps": 3,
            "pushes": 1,
            "level_index": 0,
        }
        self.assertTrue(scene.board_service.has_any_pushable_box(scene.board_state))
        self.assertFalse(scene.board_service.is_state_solvable(scene.board_state))
        scene._attempt_move("right")
        self.assertGreater(scene.restart_pending_until, 0.0)
        with patch("time.time", return_value=scene.restart_pending_until + 0.01):
            scene.update()
        self.assertEqual(scene.board_state["player"], initial_player)
        self.assertEqual(manager.sound_manager.wrong_calls, 1)

    def test_push_and_clear_play_sounds(self):
        manager = _ManagerStub()
        scene = FusionPushBoxScene(manager)
        scene._start_game()
        scene.board_state = {
            "width": 5,
            "height": 5,
            "walls": {(0, 0)},
            "targets": {(3, 1)},
            "boxes": {(2, 1)},
            "player": (1, 1),
            "steps": 0,
            "pushes": 0,
            "level_index": 0,
        }
        scene._attempt_move("right")
        self.assertEqual(manager.sound_manager.correct_calls, 1)
        self.assertEqual(manager.sound_manager.completed_calls, 1)

    def test_pending_restart_blocks_moves_until_timeout(self):
        manager = _ManagerStub()
        scene = FusionPushBoxScene(manager)
        scene._start_game()
        scene.restart_pending_until = __import__("time").time() + 5.0
        scene.board_state["player"] = (4, 4)
        scene.handle_events([pygame.event.Event(pygame.KEYDOWN, key=pygame.K_LEFT)])
        self.assertEqual(scene.board_state["player"], (4, 4))

    def test_glasses_mode_keeps_player_red_and_boxes_blue(self):
        manager = _ManagerStub()
        scene = FusionPushBoxScene(manager)
        scene.mode = scene.MODE_GLASSES
        scene.filter_direction = scene.FILTER_LR
        scene.board_state = {
            "width": 5,
            "height": 5,
            "walls": set(),
            "targets": set(),
            "boxes": {(3, 2)},
            "player": (1, 2),
            "steps": 0,
            "pushes": 0,
            "level_index": 0,
        }
        screen = pygame.Surface((scene.width, scene.height), pygame.SRCALPHA)
        scene._draw_play_board(screen)

        cell, offset_x, offset_y = scene._grid_metrics()
        player_center = (
            scene.board_rect.x + offset_x + cell + cell // 2,
            scene.board_rect.y + offset_y + 2 * cell + cell // 2,
        )
        box_center = (
            scene.board_rect.x + offset_x + 3 * cell + cell // 2,
            scene.board_rect.y + offset_y + 2 * cell + cell // 2,
        )

        player_pixel = screen.get_at(player_center)
        box_pixel = screen.get_at(box_center)

        self.assertEqual(player_pixel[:3], (255, 0, 0))
        self.assertEqual(box_pixel[:3], (0, 0, 255))


if __name__ == "__main__":
    unittest.main()
