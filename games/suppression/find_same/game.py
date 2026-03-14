from core.game_contract import GameDescriptor

from .scenes.root_scene import FindSameScene


def create_scene(manager):
    return FindSameScene(manager)


def build_descriptor():
    return GameDescriptor(
        game_id="suppression.find_same",
        category="suppression",
        name="Weak Eye Match Same",
        factory=create_scene,
        name_key="game.suppression.find_same",
    )

