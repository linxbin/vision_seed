from core.game_contract import GameDescriptor
from games.common.arcade_training.scene import ArcadeGameConfig, ArcadeTrainingScene

CONFIG = ArcadeGameConfig(
    game_id="simultaneous.spot_difference",
    category="simultaneous",
    name="Binocular Spot Difference",
    name_key="game.simultaneous.spot_difference",
    title_key="spot_difference.title",
    subtitle_key="spot_difference.subtitle",
    guide_key="spot_difference.play.guide",
    metric_label_key="spot_difference.metric.label",
    help_steps=("spot_difference.help.step1", "spot_difference.help.step2", "spot_difference.help.step3"),
    mechanic_type="spot_difference",
    theme_color=(92, 146, 214),
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
