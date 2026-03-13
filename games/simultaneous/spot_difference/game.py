from core.game_contract import GameDescriptor
from .scenes.root_scene import SpotDifferenceScene


def create_scene(manager):
    return SpotDifferenceScene(manager)


def build_descriptor():
    return GameDescriptor(
        game_id="simultaneous.spot_difference",
        category="simultaneous",
        name="Binocular Spot Difference",
        factory=create_scene,
        name_key="game.simultaneous.spot_difference",
    )
