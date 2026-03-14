from core.game_contract import GameDescriptor

from .scenes.root_scene import FruitSliceScene


def create_scene(manager):
    return FruitSliceScene(manager)


def build_descriptor():
    return GameDescriptor(
        game_id="amblyopia.fruit_slice",
        category="amblyopia",
        name="Fruit Slice Focus",
        factory=create_scene,
        name_key="game.amblyopia.fruit_slice",
    )

