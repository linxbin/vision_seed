from core.game_contract import GameDescriptor
from .scenes.root_scene import CatchFruitScene


def create_scene(manager):
    return CatchFruitScene(manager)


def build_descriptor():
    return GameDescriptor(
        game_id="accommodation.catch_fruit",
        category="accommodation",
        name="Catch Fruit Focus",
        factory=create_scene,
        name_key="game.accommodation.catch_fruit",
    )

