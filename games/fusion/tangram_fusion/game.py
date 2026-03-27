from core.game_contract import GameDescriptor

from .scenes.root_scene import TangramFusionScene


def create_scene(manager):
    return TangramFusionScene(manager)


def build_descriptor():
    return GameDescriptor(
        game_id="fusion.tangram_fusion",
        category="fusion",
        name="Tangram Fusion",
        factory=create_scene,
        name_key="game.fusion.tangram_fusion",
    )

