from core.game_contract import GameDescriptor

from .scenes.root_scene import RingFlightScene


def create_scene(manager):
    return RingFlightScene(manager)


def build_descriptor():
    return GameDescriptor(
        game_id="stereopsis.ring_flight",
        category="stereopsis",
        name="Stereo Ring Flight",
        factory=create_scene,
        name_key="game.stereopsis.ring_flight",
    )
