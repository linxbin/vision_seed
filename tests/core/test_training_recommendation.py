import unittest
from unittest.mock import Mock

from core.training_recommendation import build_daily_plan, build_daily_suggestion
from core.game_contract import GameDescriptor


class _RegistryStub:
    def get_categories(self):
        return [
            {"id": "accommodation", "name_key": "category.accommodation"},
            {"id": "simultaneous", "name_key": "category.simultaneous"},
            {"id": "fusion", "name_key": "category.fusion"},
        ]

    def get_games_by_category(self, category_id):
        mapping = {
            "accommodation": [GameDescriptor("accommodation.catch_fruit", "accommodation", "Catch", lambda m: None, "game.accommodation.catch_fruit")],
            "simultaneous": [GameDescriptor("simultaneous.spot_difference", "simultaneous", "Spot", lambda m: None, "game.simultaneous.spot_difference")],
            "fusion": [GameDescriptor("fusion.puzzle_fusion", "fusion", "Puzzle", lambda m: None, "game.fusion.puzzle_fusion")],
        }
        return mapping.get(category_id, [])


class _DataStub:
    def __init__(self, sessions):
        self.sessions = sessions

    def get_latest_session(self, game_id=None):
        return self.sessions.get(game_id, {})


class _ManagerStub:
    def __init__(self, sessions):
        self.game_registry = _RegistryStub()
        self.data_manager = _DataStub(sessions)

    def t(self, key, **kwargs):
        values = {
            "category.accommodation": "Accommodation",
            "category.simultaneous": "Simultaneous",
            "category.fusion": "Fusion",
            "game.accommodation.catch_fruit": "Catch Fruit",
            "game.simultaneous.spot_difference": "Spot Difference",
            "game.fusion.puzzle_fusion": "Puzzle Fusion",
            "menu.recommend.none": "none",
            "menu.recommend.start_fresh": "fresh-first",
            "menu.recommend.review_focus": f"review {kwargs.get('category', '')}",
        }
        return values.get(key, key)


class TrainingRecommendationTests(unittest.TestCase):
    def test_untrained_categories_are_prioritized(self):
        manager = _ManagerStub({
            "accommodation.catch_fruit": {"timestamp": "2026-03-12T09:00:00", "accuracy_rate": 92.0},
        })
        plans = build_daily_plan(manager)
        self.assertEqual(plans[0]["category_id"], "fusion")
        self.assertEqual(plans[1]["category_id"], "simultaneous")
        self.assertEqual(plans[2]["category_id"], "accommodation")

    def test_suggestion_prefers_fresh_start(self):
        manager = _ManagerStub({})
        plans = build_daily_plan(manager)
        self.assertEqual(build_daily_suggestion(manager, plans), "fresh-first")


if __name__ == "__main__":
    unittest.main()
