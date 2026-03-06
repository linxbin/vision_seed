from core.game_contract import GameDescriptor
from .scenes.menu_scene import ETrainingMenuScene


def create_scene(manager):
    return ETrainingMenuScene(manager)


def build_descriptor():
    return GameDescriptor(
        game_id="accommodation.e_orientation",
        category="accommodation",
        name="E Orientation Training",
        factory=create_scene,
        name_key="game.accommodation.e_orientation",
    )
