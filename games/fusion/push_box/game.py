from core.game_contract import GameDescriptor

from .scenes.root_scene import FusionPushBoxScene


def create_scene(manager):
    return FusionPushBoxScene(manager)


def build_descriptor():
    return GameDescriptor(
        game_id="fusion.push_box",
        category="fusion",
        name="Fusion Push Box",
        factory=create_scene,
        name_key="game.fusion.push_box",
    )
