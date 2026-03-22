from typing import Dict, List, Optional

from games.accommodation import build_catch_fruit_descriptor, build_descriptor as build_accommodation_descriptor, build_snake_descriptor
from games.amblyopia import build_fruit_slice_descriptor, build_precision_aim_descriptor, build_whack_a_mole_descriptor
from games.fusion import build_path_fusion_descriptor, build_push_box_descriptor, build_tetris_descriptor
from games.simultaneous import build_eye_find_patterns_descriptor, build_pong_descriptor, build_spot_difference_descriptor
from games.stereopsis import build_depth_grab_descriptor, build_ring_flight_descriptor
from games.suppression import build_find_same_descriptor, build_red_blue_catch_descriptor, build_weak_eye_key_descriptor

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
        self.register(build_catch_fruit_descriptor())
        self.register(build_snake_descriptor())
        self.register(build_eye_find_patterns_descriptor())
        self.register(build_spot_difference_descriptor())
        self.register(build_pong_descriptor())
        self.register(build_push_box_descriptor())
        self.register(build_tetris_descriptor())
        self.register(build_path_fusion_descriptor())
        self.register(build_weak_eye_key_descriptor())
        self.register(build_find_same_descriptor())
        self.register(build_red_blue_catch_descriptor())
        self.register(build_depth_grab_descriptor())
        self.register(build_ring_flight_descriptor())
        self.register(build_precision_aim_descriptor())
        self.register(build_whack_a_mole_descriptor())
        self.register(build_fruit_slice_descriptor())

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
