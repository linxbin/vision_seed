import unittest

from core.game_registry import CATEGORY_LABELS, GameRegistry


class GameRegistryTests(unittest.TestCase):
    def test_categories_are_available(self):
        registry = GameRegistry()
        categories = registry.get_categories()
        self.assertEqual(len(categories), 6)
        ids = {item["id"] for item in categories}
        self.assertEqual(ids, set(CATEGORY_LABELS.keys()))

    def test_builtin_games_registered(self):
        registry = GameRegistry()
        expected = {
            "accommodation.e_orientation": "accommodation",
            "accommodation.catch_fruit": "accommodation",
            "accommodation.snake": "accommodation",
            "simultaneous.eye_find_patterns": "simultaneous",
            "simultaneous.spot_difference": "simultaneous",
            "simultaneous.pong": "simultaneous",
            "fusion.push_box": "fusion",
            "fusion.tetris": "fusion",
            "fusion.path_fusion": "fusion",
            "suppression.weak_eye_key": "suppression",
            "suppression.find_same": "suppression",
            "suppression.red_blue_catch": "suppression",
            "stereopsis.depth_grab": "stereopsis",
            "stereopsis.brick_breaker": "stereopsis",
            "stereopsis.frogger": "stereopsis",
            "amblyopia.precision_aim": "amblyopia",
            "amblyopia.whack_a_mole": "amblyopia",
            "amblyopia.fruit_slice": "amblyopia",
        }
        for game_id, category in expected.items():
            game = registry.get_game(game_id)
            self.assertIsNotNone(game, game_id)
            self.assertEqual(game.category, category)


if __name__ == "__main__":
    unittest.main()
