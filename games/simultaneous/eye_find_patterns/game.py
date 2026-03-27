from core.game_contract import GameDescriptor
from .scenes.game_scene import EyeFindPatternsScene


def create_scene(manager):
    return EyeFindPatternsScene(manager)


def build_descriptor():
    return GameDescriptor(
        game_id="simultaneous.eye_find_patterns",
        category="simultaneous",
        name="Eye Find Patterns",
        factory=create_scene,
        name_key="game.simultaneous.eye_find_patterns",
    )
