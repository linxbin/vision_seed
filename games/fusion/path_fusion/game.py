from core.game_contract import GameDescriptor

from .scenes.root_scene import PathFusionScene


def create_scene(manager):
    return PathFusionScene(manager)


def build_descriptor():
    return GameDescriptor(
        game_id="fusion.path_fusion",
        category="fusion",
        name="Path Fusion",
        factory=create_scene,
        name_key="game.fusion.path_fusion",
    )

