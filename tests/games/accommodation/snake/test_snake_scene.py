import os
import time
import unittest

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")

import pygame

from games.accommodation.snake.scenes.root_scene import SnakeFocusScene


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


class SnakeFocusSceneTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        pygame.init()

    @classmethod
    def tearDownClass(cls):
        pygame.quit()

    def test_start_session_from_home(self):
        scene = SnakeFocusScene(_ManagerStub())
        scene.handle_events([pygame.event.Event(pygame.KEYDOWN, key=pygame.K_1)])
        self.assertEqual(scene.state, scene.STATE_PLAY)

    def test_food_increases_score(self):
        manager = _ManagerStub()
        scene = SnakeFocusScene(manager)
        scene._start_game()
        head = scene.round_data["snake"][0]
        direction = scene.round_data["direction"]
        scene.round_data["food"] = (head[0] + direction[0], head[1] + direction[1])
        scene._step_snake()
        self.assertEqual(scene.scoring.food_count, 1)
        self.assertGreater(scene.scoring.score, 0)
        self.assertEqual(manager.sound_manager.correct_calls, 1)

    def test_collision_counts_failure(self):
        manager = _ManagerStub()
        scene = SnakeFocusScene(manager)
        scene._start_game()
        scene.round_data["snake"] = [(0, 0), (1, 0), (2, 0)]
        scene.round_data["direction"] = (-1, 0)
        scene.round_data["pending_direction"] = (-1, 0)
        scene._step_snake()
        self.assertEqual(scene.scoring.collision_count, 1)
        self.assertEqual(manager.sound_manager.wrong_calls, 1)

    def test_finish_saves_result(self):
        manager = _ManagerStub()
        scene = SnakeFocusScene(manager)
        scene._start_game()
        scene.session.session_started_at = time.time() - scene._session_seconds()
        scene.update()
        self.assertEqual(scene.state, scene.STATE_RESULT)
        self.assertEqual(manager.data_manager.saved[-1]["game_id"], "accommodation.snake")
        self.assertEqual(manager.sound_manager.completed_calls, 1)

    def test_play_layout_keeps_guide_above_board_and_border_visible(self):
        scene = SnakeFocusScene(_ManagerStub())
        scene._start_game()
        screen = pygame.Surface((scene.width, scene.height))
        scene.draw(screen)
        inner_board = scene._inner_board_rect()
        self.assertLess(scene.play_area.y - 26, inner_board.y)
        border_color = (176, 204, 176)
        self.assertEqual(screen.get_at((inner_board.centerx, inner_board.y + 1))[:3], border_color)
        self.assertEqual(screen.get_at((inner_board.x + 1, inner_board.centery))[:3], border_color)
        self.assertEqual(screen.get_at((inner_board.centerx, inner_board.bottom - 2))[:3], border_color)
        self.assertEqual(screen.get_at((inner_board.right - 2, inner_board.centery))[:3], border_color)
