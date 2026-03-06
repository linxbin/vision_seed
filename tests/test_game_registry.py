import unittest

from core.game_registry import CATEGORY_LABELS, GameRegistry


class GameRegistryTests(unittest.TestCase):
    def test_categories_are_available(self):
        registry = GameRegistry()
        categories = registry.get_categories()
        self.assertEqual(len(categories), 6)
        ids = {item["id"] for item in categories}
        self.assertEqual(ids, set(CATEGORY_LABELS.keys()))

    def test_builtin_game_registered(self):
        registry = GameRegistry()
        game = registry.get_game("accommodation.e_orientation")
        self.assertIsNotNone(game)
        self.assertEqual(game.category, "accommodation")
        self.assertEqual(game.name, "E Orientation Training")


if __name__ == "__main__":
    unittest.main()
