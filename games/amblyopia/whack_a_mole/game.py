from core.game_contract import GameDescriptor

from .scenes.root_scene import WhackAMoleScene


def create_scene(manager):
    return WhackAMoleScene(manager)


def build_descriptor():
    return GameDescriptor(
        game_id="amblyopia.whack_a_mole",
        category="amblyopia",
        name="Whack A Mole Vision",
        factory=create_scene,
        name_key="game.amblyopia.whack_a_mole",
    )

