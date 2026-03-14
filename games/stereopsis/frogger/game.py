from core.game_contract import GameDescriptor

from .scenes.root_scene import FroggerScene


def create_scene(manager):
    return FroggerScene(manager)


def build_descriptor():
    return GameDescriptor(
        game_id="stereopsis.frogger",
        category="stereopsis",
        name="Stereo Frogger",
        factory=create_scene,
        name_key="game.stereopsis.frogger",
    )

