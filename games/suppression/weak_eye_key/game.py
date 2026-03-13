from core.game_contract import GameDescriptor

from .scenes.root_scene import WeakEyeKeyScene


def create_scene(manager):
    return WeakEyeKeyScene(manager)


def build_descriptor():
    return GameDescriptor(
        game_id="suppression.weak_eye_key",
        category="suppression",
        name="Weak Eye Key Hunt",
        factory=create_scene,
        name_key="game.suppression.weak_eye_key",
    )
