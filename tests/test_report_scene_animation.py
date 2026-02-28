import os
import unittest

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")

import pygame

from scenes.report_scene import ReportScene


class _AdaptiveStub:
    def evaluate(self, **_kwargs):
        return {}


class _DataStub:
    def get_all_sessions(self):
        return []


class _ManagerStub:
    def __init__(self):
        self.settings = {"language": "en-US", "start_level": 3, "total_questions": 30}
        self.current_result = {"correct": 8, "wrong": 2, "total": 10, "duration": 12.5, "max_combo": 4}
        self.data_manager = _DataStub()

    def evaluate_adaptive_level(self):
        return {}

    def t(self, key, **kwargs):
        if kwargs:
            try:
                return key.format(**kwargs)
            except Exception:
                return key
        return key


class ReportSceneAnimationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        pygame.init()

    @classmethod
    def tearDownClass(cls):
        pygame.quit()

    def test_animation_progress_clamps_between_zero_and_one(self):
        scene = ReportScene(_ManagerStub())
        scene.enter_started_at = 100.0
        self.assertEqual(scene._animation_progress(now=99.0), 0.0)
        self.assertAlmostEqual(scene._animation_progress(now=100.425), 0.5, places=2)
        self.assertEqual(scene._animation_progress(now=101.5), 1.0)

    def test_card_progress_respects_stagger_delay(self):
        scene = ReportScene(_ManagerStub())
        p0 = scene._card_progress(0, 0.2)
        p3_early = scene._card_progress(3, 0.2)
        p3_late = scene._card_progress(3, 0.7)

        self.assertGreater(p0, 0.0)
        self.assertEqual(p3_early, 0.0)
        self.assertGreater(p3_late, 0.0)

    def test_on_enter_snapshots_final_result(self):
        manager = _ManagerStub()
        scene = ReportScene(manager)
        scene.on_enter()

        self.assertEqual(scene.final_result["correct"], 8)
        self.assertEqual(scene.final_result["wrong"], 2)
        self.assertEqual(scene.final_result["total"], 10)
        self.assertEqual(scene.final_result["max_combo"], 4)
        self.assertGreater(scene.enter_started_at, 0.0)

if __name__ == "__main__":
    unittest.main()
