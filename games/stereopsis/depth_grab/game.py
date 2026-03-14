from core.game_contract import GameDescriptor
from .scenes.root_scene import DepthGrabScene


def create_scene(manager):
    return DepthGrabScene(manager)


def build_descriptor():
    return GameDescriptor(
        game_id="stereopsis.depth_grab",
        category="stereopsis",
        name="Depth Grab Stars",
        factory=create_scene,
        name_key="game.stereopsis.depth_grab",
    )

