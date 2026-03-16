import os
import sys
import unittest

import pygame

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tests.ui_test_base import UITestCase
from scenes.category_scene import CategoryScene


class _RegistryStub:
    def __init__(self):
        self._categories = [
            {"id": "accommodation", "name": "Accommodation Training", "name_key": "category.accommodation"},
        ]
        self._games = [
            type("GameStub", (), {"game_id": "accommodation.e_orientation", "name": "E Orientation", "name_key": ""})(),
            type("GameStub", (), {"game_id": "accommodation.catch_fruit", "name": "Catch Fruit", "name_key": ""})(),
        ]

    def get_categories(self):
        return self._categories

    def get_games_by_category(self, category_id):
        return self._games if category_id == "accommodation" else []


class _DataManagerStub:
    def get_latest_session(self, _game_id):
        return None


class _ManagerStub:
    def __init__(self):
        self.settings = {"language": "en-US"}
        self.active_category = "accommodation"
        self.active_game_id = None
        self.game_registry = _RegistryStub()
        self.data_manager = _DataManagerStub()
        self.last_scene = None

    def t(self, key, **kwargs):
        translations = {
            "category.accommodation": "Accommodation Training",
            "category.empty": "No games in this category",
            "category.hint": "Esc or Back: Return",
            "common.back": "Back",
        }
        template = translations.get(key, key)
        if kwargs:
            try:
                return template.format(**kwargs)
            except Exception:
                return template
        return template

    def set_scene(self, name):
        self.last_scene = name


class TestCategorySceneUI(UITestCase):
    def setUp(self):
        super().setUp()
        self.manager = _ManagerStub()
        self.scene = CategoryScene(self.manager)

    def test_arrow_keys_move_focus_and_enter_opens_game(self):
        self.capture_frame(self.scene, self.simulate_key_event(pygame.K_DOWN))
        self.assertEqual(self.scene.focused_index, 1)
        self.capture_frame(self.scene, self.simulate_key_event(pygame.K_RETURN))
        self.assertEqual(self.manager.active_game_id, "accommodation.catch_fruit")
        self.assertEqual(self.manager.last_scene, "game_host")

    def test_focus_can_reach_back_button(self):
        self.capture_frame(self.scene, self.simulate_key_event(pygame.K_UP))
        self.assertEqual(self.scene.focused_index, len(self.scene._items))
        self.capture_frame(self.scene, self.simulate_key_event(pygame.K_SPACE))
        self.assertEqual(self.manager.last_scene, "menu")


if __name__ == "__main__":
    unittest.main()
