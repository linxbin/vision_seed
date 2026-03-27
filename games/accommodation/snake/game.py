from core.game_contract import GameDescriptor

from .scenes.root_scene import SnakeFocusScene


def create_scene(manager):
    return SnakeFocusScene(manager)


def build_descriptor():
    return GameDescriptor(
        game_id="accommodation.snake",
        category="accommodation",
        name="Snake Focus Track",
        factory=create_scene,
        name_key="game.accommodation.snake",
    )

