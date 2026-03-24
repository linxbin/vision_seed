from core.game_contract import GameDescriptor

from .scenes.root_scene import PopNearestScene


def create_scene(manager):
    return PopNearestScene(manager)


def build_descriptor():
    return GameDescriptor(
        game_id="stereopsis.pop_nearest",
        category="stereopsis",
        name="Stereo Balloon Pop",
        factory=create_scene,
        name_key="game.stereopsis.pop_nearest",
    )
