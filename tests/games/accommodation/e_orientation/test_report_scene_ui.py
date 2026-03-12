import os
import sys
import unittest
from unittest.mock import patch

import pygame

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from games.accommodation.e_orientation.i18n import TRANSLATIONS
from games.accommodation.e_orientation.scenes.report_scene import ReportScene
from tests.ui_test_base import UITestCase


class TestReportSceneUI(UITestCase):
    def setUp(self):
        super().setUp()
        self.mock_manager = self.create_mock_scene_manager()
        self.translation_overrides = {}
        self.mock_manager.t = self._translate
        self.mock_manager.current_result = {
            "correct": 25,
            "wrong": 5,
            "total": 30,
            "duration": 120.5,
            "max_combo": 8,
        }
        self.mock_manager.data_manager.get_all_sessions.return_value = [
            {"timestamp": "2026-03-02T13:00:00", "accuracy_rate": 83.3},
            {"timestamp": "2026-03-02T12:00:00", "accuracy_rate": 75.0},
        ]
        self.mock_manager.evaluate_adaptive_level.return_value = {"suggested_level": 4, "reason": "improved"}
        self.scene = ReportScene(self.mock_manager)
        self.scene.on_enter()

    def _translate(self, key, **kwargs):
        language = self.mock_manager.settings.get("language", "en-US")
        override_map = self.translation_overrides.get(language, {})
        template = override_map.get(key)
        if template is None:
            template = TRANSLATIONS.get(language, TRANSLATIONS["en-US"]).get(
                key,
                TRANSLATIONS["en-US"].get(key, key),
            )
        try:
            return template.format(**kwargs)
        except KeyError:
            return template

    def test_scene_initialization(self):
        self.assertIsNotNone(self.scene.manager)
        self.assertEqual(len(self.scene.cards), 6)
        self.assertIsNotNone(self.scene.retry_button_rect)
        self.assertIsNotNone(self.scene.menu_button_rect)
        self.assertEqual(self.scene.final_result["correct"], 25)
        self.assertEqual(self.scene.final_result["total"], 30)

    def test_report_rendering_basic(self):
        frame = self.capture_frame(self.scene)
        center_x = frame.get_width() // 2
        center_y = frame.get_height() // 2
        center_color = self.get_surface_average_color(frame, (center_x - 150, center_y - 150, 300, 300))
        self.assertGreater(sum(center_color[:3]), 10)

    def test_data_card_display(self):
        frame = self.capture_frame(self.scene)
        initial_sum = sum(self.get_surface_average_color(frame)[:3])

        self.mock_manager.current_result["correct"] = 30
        self.scene.on_enter()
        updated_frame = self.capture_frame(self.scene)
        updated_sum = sum(self.get_surface_average_color(updated_frame)[:3])

        if initial_sum == updated_sum:
            with patch("time.time", return_value=self.scene.enter_started_at + 10):
                final_frame = self.capture_frame(self.scene)
                final_sum = sum(self.get_surface_average_color(final_frame)[:3])
                self.assertNotEqual(initial_sum, final_sum)
        else:
            self.assertNotEqual(initial_sum, updated_sum)

    def test_button_interaction(self):
        retry_pos = (self.scene.retry_button_rect.centerx, self.scene.retry_button_rect.centery)
        self.set_mouse_position(*retry_pos)
        click_events = self.simulate_mouse_event(pygame.MOUSEBUTTONDOWN, retry_pos, button=1)
        self.capture_frame(self.scene, click_events)
        self.mock_manager.set_scene.assert_called_with("training")

    def test_action_button_content_fits_rect(self):
        for rect, key, icon_name in (
            (self.scene.retry_button_rect, "report.retry", "check"),
            (self.scene.menu_button_rect, "report.back_menu", "cross"),
        ):
            content_width = self.scene._button_content_width(self.mock_manager.t(key), icon_name)
            available_width = rect.width - self.scene.BUTTON_HORIZONTAL_PADDING * 2
            self.assertGreaterEqual(available_width, content_width)

    def test_language_change_reflows_action_buttons(self):
        initial_width = self.scene.menu_button_rect.width
        self.translation_overrides["zh-CN"] = {"report.back_menu": "Return to Menu Overview"}
        self.mock_manager.settings["language"] = "zh-CN"

        self.capture_frame(self.scene)

        self.assertNotEqual(initial_width, self.scene.menu_button_rect.width)
        content_width = self.scene._button_content_width(self.mock_manager.t("report.back_menu"), "cross")
        available_width = self.scene.menu_button_rect.width - self.scene.BUTTON_HORIZONTAL_PADDING * 2
        self.assertGreaterEqual(available_width, content_width)


if __name__ == "__main__":
    unittest.main()
