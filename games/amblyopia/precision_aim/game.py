from core.game_contract import GameDescriptor
from .scenes.root_scene import PrecisionAimScene


def create_scene(manager):
    return PrecisionAimScene(manager)


def build_descriptor():
    return GameDescriptor(
        game_id="amblyopia.precision_aim",
        category="amblyopia",
        name="Precision Aim Target",
        factory=create_scene,
        name_key="game.amblyopia.precision_aim",
    )

