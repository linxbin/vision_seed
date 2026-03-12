import os
import sys
import unittest

import pygame

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from games.accommodation.e_orientation.scenes.history_scene import HistoryScene
from tests.ui_test_base import UITestCase


class TestHistorySceneUI(UITestCase):
    def setUp(self):
        super().setUp()
        self.mock_manager = self.create_mock_scene_manager()
        self.mock_manager.data_manager.get_all_sessions.return_value = [
            {
                "timestamp": "2026-03-02T13:00:00",
                "difficulty_level": 3,
                "e_size_px": 30,
                "total_questions": 30,
                "correct_count": 25,
                "wrong_count": 5,
                "duration_seconds": 120.5,
                "accuracy_rate": 83.3,
            },
            {
                "timestamp": "2026-03-02T12:00:00",
                "difficulty_level": 2,
                "e_size_px": 20,
                "total_questions": 20,
                "correct_count": 18,
                "wrong_count": 2,
                "duration_seconds": 80.0,
                "accuracy_rate": 90.0,
            },
        ]
        self.scene = HistoryScene(self.mock_manager)
        self.scene.on_enter()

    def test_scene_initialization(self):
        self.assertIsNotNone(self.scene.manager)
        self.assertEqual(len(self.scene.raw_records), 2)
        self.assertEqual(len(self.scene.filtered_records), 2)
        self.assertIsNotNone(self.scene.date_all_rect)
        self.assertIsNotNone(self.scene.level_value_rect)
        self.assertIsNotNone(self.scene.sort_time_rect)

    def test_back_button_uses_menu_sized_chip(self):
        self.assertEqual(self.scene.back_button_rect.size, (78, 34))

    def test_history_rendering_basic(self):
        frame = self.capture_frame(self.scene)
        center_x = frame.get_width() // 2
        center_y = frame.get_height() // 2
        center_color = self.get_surface_average_color(frame, (center_x - 150, center_y - 150, 300, 300))
        self.assertGreater(sum(center_color[:3]), 10)

    def test_filter_controls_interaction(self):
        date_7d_pos = (self.scene.date_7d_rect.centerx, self.scene.date_7d_rect.centery)
        self.set_mouse_position(*date_7d_pos)
        click_events = self.simulate_mouse_event(pygame.MOUSEBUTTONDOWN, date_7d_pos, button=1)
        self.capture_frame(self.scene, click_events)
        self.assertEqual(self.scene.date_filter, "7d")

    def test_back_button_navigation(self):
        back_pos = (self.scene.back_button_rect.centerx, self.scene.back_button_rect.centery)
        self.set_mouse_position(*back_pos)
        click_events = self.simulate_mouse_event(pygame.MOUSEBUTTONDOWN, back_pos, button=1)
        self.capture_frame(self.scene, click_events)
        self.mock_manager.set_scene.assert_called_with("menu")


if __name__ == "__main__":
    unittest.main()
