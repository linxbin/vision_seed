import pygame
import sys
import os
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tests.ui_test_base import UITestCase
from scenes.menu_scene import MenuScene


class TestMenuSceneUI(UITestCase):
    def setUp(self):
        super().setUp()
        self.mock_manager = self.create_mock_scene_manager()
        self.scene = MenuScene(self.mock_manager)

    def test_scene_initialization(self):
        self.assertIsNotNone(self.scene.manager)
        self.assertEqual(len(self.scene.menu_options), 3)
        self.assertEqual(len(self.scene.templates), 0)
        self.assertLessEqual(len(self.scene.recommendations), 3)
        first_option = self.scene.menu_options[0]
        self.assertEqual(first_option["key"], "menu.start_training")
        self.assertEqual(first_option["scene"], "training")

    def test_menu_rendering_basic(self):
        frame = self.capture_frame(self.scene)
        center_x = frame.get_width() // 2
        center_y = frame.get_height() // 2
        center_color = self.get_surface_average_color(frame, (center_x - 100, center_y - 100, 200, 200))
        self.assertGreater(sum(center_color[:3]), 10)

    def test_recommendation_panel_renders(self):
        frame = self.capture_frame(self.scene)
        panel_color = self.get_surface_average_color(frame, (180, 520, 540, 100))
        self.assertGreater(sum(panel_color[:3]), 30)

    def test_recent_completion_uses_latest_game_results(self):
        latest_sessions = [
            {"game_id": "simultaneous.pong", "accuracy_rate": 88.5, "duration_seconds": 120.0},
            {"game_id": "simultaneous.spot_difference", "accuracy_rate": 76.0, "duration_seconds": 95.0},
        ]
        self.mock_manager.data_manager.get_all_sessions.return_value = latest_sessions
        self.mock_manager.game_registry.get_game.side_effect = lambda game_id: type(
            "GameStub",
            (),
            {
                "game_id": game_id,
                "name": game_id,
                "name_key": "game.simultaneous.pong" if game_id == "simultaneous.pong" else "game.simultaneous.spot_difference",
            },
        )()
        self.scene._build_items()
        self.assertEqual(len(self.scene.recent_completions), 2)
        self.assertEqual(self.scene.recent_completions[0]["game_id"], "simultaneous.pong")
        visible_lines = min(len(self.scene.recommendations), self.scene._recommendation_lines)
        last_recommendation_y = self.scene.recommend_panel.y + 72 + max(0, visible_lines - 1) * 18 + 20
        self.assertGreater(self.scene._recent_row_y, last_recommendation_y)

    def test_mouse_hover_interaction(self):
        first_menu_rect = self.scene._items[1]["rect"]
        hover_pos = (first_menu_rect.centerx, first_menu_rect.centery)
        self.set_mouse_position(*hover_pos)
        hover_frame = self.capture_frame(self.scene)
        self.set_mouse_position(0, 0)
        initial_frame = self.capture_frame(self.scene)
        initial_sum = sum(self.get_surface_average_color(initial_frame)[:3])
        hover_sum = sum(self.get_surface_average_color(hover_frame)[:3])
        self.assertNotEqual(initial_sum, hover_sum)

    def test_menu_click_navigation(self):
        first_option = None
        for option in self.scene.menu_options:
            if option["scene"] == "training":
                first_option = option
                break
        self.assertIsNotNone(first_option)
        click_pos = (first_option["rect"].centerx, first_option["rect"].centery)
        self.set_mouse_position(*click_pos)
        click_events = self.simulate_mouse_event(pygame.MOUSEBUTTONDOWN, click_pos, button=1)
        self.capture_frame(self.scene, click_events)
        self.mock_manager.set_scene.assert_called_with("category")

    def test_keyboard_navigation_uses_focus_and_enter(self):
        events = self.simulate_key_event(pygame.K_DOWN)
        self.capture_frame(self.scene, events)
        self.assertEqual(self.scene.focused_index, 1)
        self.capture_frame(self.scene, self.simulate_key_event(pygame.K_RETURN))
        self.assertEqual(self.mock_manager.active_category, "simultaneous")
        self.mock_manager.set_scene.assert_called_with("category")

    def test_small_window_long_recommendation_text_still_renders(self):
        self.scene.recommendation_hint = (
            "Review the weaker binocular category first, then complete a short fresh session before moving on."
        )
        self.scene.recommendations = [
            {"game_name": "Very Long Simultaneous Vision Training Name", "reason_key": "reason.one", "accuracy": 82.4},
            {"game_name": "Another Extended Recommendation Label", "reason_key": "reason.two", "accuracy": 76.1},
        ]
        self.scene.recent_completions = [
            {"game_name": "Long Recent Game Name", "accuracy": 91.2, "game_id": "simultaneous.pong"},
        ]
        def mock_t(key, **kwargs):
            values = {
                "menu.recommend.title": "Today's Recommended Order",
                "menu.recent.title": "Recent",
                "menu.recent.none": "No session yet",
                "reason.one": "review (82.4%)",
                "reason.two": "fresh today",
                "menu.title": "VisionSeed",
                "menu.multigame_subtitle": "Multi-Game Training",
                "menu.hint": "Shortcuts: 1-9",
                "category.accommodation": "Accommodation Training",
                "category.simultaneous": "Simultaneous Vision Training",
                "category.fusion": "Fusion Training",
                "category.suppression": "Suppression Release Training",
                "category.stereopsis": "Stereopsis Training",
                "category.amblyopia": "Amblyopia Training",
                "menu.system_settings": "System Settings",
                "menu.exit": "Exit",
                "menu.recent.item": "{game} ({accuracy}%)",
            }
            template = values.get(key, key)
            return template.format(**kwargs) if kwargs else template

        self.mock_manager.t = mock_t
        self.scene.on_resize(840, 640)
        frame = self.capture_frame(self.scene)
        panel_color = self.get_surface_average_color(frame, (30, 400, 500, 170))
        self.assertGreater(sum(panel_color[:3]), 30)


if __name__ == '__main__':
    unittest.main()
