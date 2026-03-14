import os
import time
import unittest

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")

import pygame

from games.amblyopia.precision_aim.scenes.root_scene import PrecisionAimScene
from games.amblyopia.precision_aim.services.board_service import PrecisionAimBoardService


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


class PrecisionAimSceneTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        pygame.init()

    @classmethod
    def tearDownClass(cls):
        pygame.quit()

    def test_start_session_from_home(self):
        scene = PrecisionAimScene(_ManagerStub())
        scene.handle_events([pygame.event.Event(pygame.KEYDOWN, key=pygame.K_1)])
        self.assertEqual(scene.state, scene.STATE_PLAY)

    def test_center_hit_scores(self):
        manager = _ManagerStub()
        scene = PrecisionAimScene(manager)
        scene._start_game()
        scene.round_data = {
            "target_center": (200, 200),
            "anchor_center": (200, 200),
            "aim_center": [200, 200],
            "base_radius": 30,
            "current_radius": 30,
            "challenge_shift": 0.0,
            "stage_index": 1,
        }
        scene.session.round_started_at = time.time() - 1.2
        scene.session.tick(time.time())
        scene._handle_shot(200, 200)
        self.assertEqual(scene.scoring.success_count, 1)
        self.assertGreater(scene.scoring.score, 0)
        self.assertEqual(manager.sound_manager.correct_calls, 1)

    def test_miss_counts_failure(self):
        manager = _ManagerStub()
        scene = PrecisionAimScene(manager)
        scene._start_game()
        scene.round_data = {
            "target_center": (200, 200),
            "anchor_center": (200, 200),
            "aim_center": [260, 260],
            "base_radius": 20,
            "current_radius": 20,
            "challenge_shift": 0.0,
            "stage_index": 2,
        }
        scene._handle_shot(260, 260)
        self.assertEqual(scene.scoring.failure_count, 1)
        self.assertEqual(manager.sound_manager.wrong_calls, 1)

    def test_finish_saves_result(self):
        manager = _ManagerStub()
        scene = PrecisionAimScene(manager)
        scene._start_game()
        scene.scoring.success_count = 3
        scene.scoring.failure_count = 1
        scene.scoring.center_hit_count = 2
        scene.scoring.score = 52
        scene.session.session_started_at = time.time() - scene._session_seconds()
        scene.update()
        self.assertEqual(scene.state, scene.STATE_RESULT)
        self.assertEqual(manager.data_manager.saved[-1]["game_id"], "amblyopia.precision_aim")
        self.assertEqual(manager.data_manager.saved[-1]["training_metrics"]["center_hit_rate"], 66.7)
        self.assertEqual(manager.sound_manager.completed_calls, 1)

    def test_background_switches_between_checker_and_stripe(self):
        scene = PrecisionAimScene(_ManagerStub())
        scene._start_game()
        scene.background_switched_at = time.time() - 7.0
        current_mode = scene.background_mode
        scene.update()
        self.assertNotEqual(scene.background_mode, current_mode)

    def test_board_service_avoids_repeating_anchor_location(self):
        service = PrecisionAimBoardService()
        play_area = pygame.Rect(70, 136, 760, 462)
        previous_anchor = (play_area.centerx, play_area.centery)
        for _ in range(12):
            round_data = service.create_round(play_area, 1, 4, previous_anchor=previous_anchor)
            distance = ((round_data["anchor_center"][0] - previous_anchor[0]) ** 2 + (round_data["anchor_center"][1] - previous_anchor[1]) ** 2) ** 0.5
            self.assertGreaterEqual(distance, 130)

    def test_finish_result_contains_center_hit_rate(self):
        manager = _ManagerStub()
        scene = PrecisionAimScene(manager)
        scene._start_game()
        scene.scoring.success_count = 5
        scene.scoring.failure_count = 1
        scene.scoring.center_hit_count = 3
        scene.session.session_started_at = time.time() - scene._session_seconds()
        scene.update()
        self.assertEqual(scene.final_stats["center_hit_rate"], 60.0)
