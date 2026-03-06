from typing import Dict, List, Optional

from games.accommodation import build_descriptor as build_accommodation_descriptor

from .game_contract import GameDescriptor


CATEGORY_LABELS = {
    "accommodation": {"name": "Accommodation Training", "name_key": "category.accommodation"},
    "simultaneous": {"name": "Simultaneous Vision Training", "name_key": "category.simultaneous"},
    "fusion": {"name": "Fusion Training", "name_key": "category.fusion"},
    "suppression": {"name": "Suppression Release Training", "name_key": "category.suppression"},
    "stereopsis": {"name": "Stereopsis Training", "name_key": "category.stereopsis"},
    "amblyopia": {"name": "Amblyopia Training", "name_key": "category.amblyopia"},
}


class GameRegistry:
    def __init__(self):
        self._games: Dict[str, GameDescriptor] = {}
        self._register_builtin_games()

    def _register_builtin_games(self):
        self.register(build_accommodation_descriptor())

    def register(self, game: GameDescriptor):
        self._games[game.game_id] = game

    def get_categories(self) -> List[dict]:
        return [
            {
                "id": category_id,
                "name": category_value["name"],
                "name_key": category_value["name_key"],
            }
            for category_id, category_value in CATEGORY_LABELS.items()
        ]

    def get_games_by_category(self, category_id: str) -> List[GameDescriptor]:
        games = [g for g in self._games.values() if g.category == category_id]
        games.sort(key=lambda item: item.game_id)
        return games

    def get_game(self, game_id: str) -> Optional[GameDescriptor]:
        return self._games.get(game_id)
