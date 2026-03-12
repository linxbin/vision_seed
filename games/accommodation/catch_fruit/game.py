from core.game_contract import GameDescriptor
from games.common.arcade_training.scene import ArcadeGameConfig, ArcadeTrainingScene

CONFIG = ArcadeGameConfig(
    game_id="accommodation.catch_fruit",
    category="accommodation",
    name="Catch Fruit Focus",
    name_key="game.accommodation.catch_fruit",
    title_key="catch_fruit.title",
    subtitle_key="catch_fruit.subtitle",
    guide_key="catch_fruit.play.guide",
    metric_label_key="catch_fruit.metric.label",
    help_steps=("catch_fruit.help.step1", "catch_fruit.help.step2", "catch_fruit.help.step3"),
    mechanic_type="catch_fruit",
    theme_color=(96, 156, 104),
    difficulty_level=3,
)


def create_scene(manager):
    return ArcadeTrainingScene(manager, CONFIG)


def build_descriptor():
    return GameDescriptor(
        game_id=CONFIG.game_id,
        category=CONFIG.category,
        name=CONFIG.name,
        factory=create_scene,
        name_key=CONFIG.name_key,
    )
