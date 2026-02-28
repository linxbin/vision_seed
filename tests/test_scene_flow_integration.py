import os
import unittest
from datetime import datetime, timedelta

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")

import pygame

from core.scene_manager import SceneManager
from scenes.history_scene import HistoryScene


class _DummyScene:
    def __init__(self):
        self.reset_calls = 0
        self.on_enter_calls = 0
        self.on_resize_calls = 0

    def reset(self):
        self.reset_calls += 1

    def on_enter(self):
        self.on_enter_calls += 1

    def on_resize(self, _w, _h):
        self.on_resize_calls += 1


class _HistoryManagerStub:
    def __init__(self):
        self.settings = {"language": "en-US"}
        self.data_manager = None

    def t(self, key, **kwargs):
        if kwargs:
            try:
                return key.format(**kwargs)
            except Exception:
                return key
        return key


class SceneFlowIntegrationTests(unittest.TestCase):
    def test_decide_initial_scene_priority(self):
        self.assertEqual(SceneManager.decide_initial_scene(False, False), "license")
        self.assertEqual(SceneManager.decide_initial_scene(False, True), "license")
        self.assertEqual(SceneManager.decide_initial_scene(True, False), "onboarding")
        self.assertEqual(SceneManager.decide_initial_scene(True, True), "menu")

    def test_set_scene_training_calls_reset_only(self):
        manager = SceneManager.__new__(SceneManager)
        training = _DummyScene()
        manager.scenes = {"training": training}
        manager.screen_size = (900, 700)
        manager.scene = None

        SceneManager.set_scene(manager, "training")

        self.assertEqual(training.on_resize_calls, 1)
        self.assertEqual(training.reset_calls, 1)
        self.assertEqual(training.on_enter_calls, 0)

    def test_set_scene_non_training_calls_on_enter(self):
        manager = SceneManager.__new__(SceneManager)
        menu = _DummyScene()
        manager.scenes = {"menu": menu}
        manager.screen_size = (900, 700)
        manager.scene = None

        SceneManager.set_scene(manager, "menu")

        self.assertEqual(menu.on_resize_calls, 1)
        self.assertEqual(menu.on_enter_calls, 1)
        self.assertEqual(menu.reset_calls, 0)


class HistorySceneFilterIntegrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        pygame.init()

    @classmethod
    def tearDownClass(cls):
        pygame.quit()

    def _session(self, ts, level, acc):
        return {
            "timestamp": ts,
            "difficulty_level": level,
            "accuracy_rate": acc,
            "total_questions": 10,
            "correct_count": 8,
            "duration_seconds": 20.0,
        }

    def test_filters_sort_and_page_clamp(self):
        manager = _HistoryManagerStub()
        scene = HistoryScene(manager)

        now = datetime.now()
        s1 = self._session((now - timedelta(days=1)).isoformat(), 3, 75.0)
        s2 = self._session((now - timedelta(days=10)).isoformat(), 3, 92.0)
        s3 = self._session((now - timedelta(days=40)).isoformat(), 4, 88.0)
        s4 = self._session("bad-ts", 3, 99.0)
        scene.raw_records = [s1, s2, s3, s4]

        # 分页边界：先置为较大页码，后续过滤应自动钳制回有效范围
        scene.current_page = 9
        scene.records_per_page = 2
        scene.date_filter = "7d"
        scene.level_filter = 3
        scene.sort_mode = "accuracy"
        scene._apply_filters()

        self.assertEqual(len(scene.filtered_records), 1)
        self.assertEqual(scene.filtered_records[0]["accuracy_rate"], 75.0)
        self.assertEqual(scene.total_pages, 1)
        self.assertEqual(scene.current_page, 0)

        # 放开日期筛选，验证准确率排序（降序）
        scene.date_filter = "all"
        scene.level_filter = 3
        scene.sort_mode = "accuracy"
        scene._apply_filters()
        self.assertEqual([r["accuracy_rate"] for r in scene.filtered_records], [99.0, 92.0, 75.0])


if __name__ == "__main__":
    unittest.main()
