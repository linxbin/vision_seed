from core.game_contract import GameDescriptor

from .scenes.root_scene import FusionTetrisScene


def create_scene(manager):
    return FusionTetrisScene(manager)


def build_descriptor():
    return GameDescriptor(
        game_id="fusion.tetris",
        category="fusion",
        name="Fusion Tetris",
        factory=create_scene,
        name_key="game.fusion.tetris",
    )

