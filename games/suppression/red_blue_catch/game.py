from core.game_contract import GameDescriptor

from .scenes.root_scene import RedBlueCatchScene


def create_scene(manager):
    return RedBlueCatchScene(manager)


def build_descriptor():
    return GameDescriptor(
        game_id="suppression.red_blue_catch",
        category="suppression",
        name="Red Blue Catch",
        factory=create_scene,
        name_key="game.suppression.red_blue_catch",
    )

