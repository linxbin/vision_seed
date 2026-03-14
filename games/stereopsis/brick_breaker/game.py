from core.game_contract import GameDescriptor

from .scenes.root_scene import BrickBreakerScene


def create_scene(manager):
    return BrickBreakerScene(manager)


def build_descriptor():
    return GameDescriptor(
        game_id="stereopsis.brick_breaker",
        category="stereopsis",
        name="Stereo Brick Breaker",
        factory=create_scene,
        name_key="game.stereopsis.brick_breaker",
    )

