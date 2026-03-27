from core.game_contract import GameDescriptor
from .scenes.root_scene import PongScene


def create_scene(manager):
    return PongScene(manager)


def build_descriptor():
    return GameDescriptor(
        game_id="simultaneous.pong",
        category="simultaneous",
        name="Binocular Pong",
        factory=create_scene,
        name_key="game.simultaneous.pong",
    )

