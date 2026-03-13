from core.game_contract import GameDescriptor
from games.common.arcade_training.scene import ArcadeGameConfig, ArcadeTrainingScene

CONFIG = ArcadeGameConfig(
    game_id="amblyopia.precision_aim",
    category="amblyopia",
    name="Precision Aim Target",
    name_key="game.amblyopia.precision_aim",
    title_key="precision_aim.title",
    subtitle_key="precision_aim.subtitle",
    guide_key="precision_aim.play.guide",
    metric_label_key="precision_aim.metric.label",
    help_steps=("precision_aim.help.step1", "precision_aim.help.step2", "precision_aim.help.step3"),
    mechanic_type="precision_aim",
    theme_color=(208, 104, 104),
    difficulty_level=4,
    play_background_style="amblyopia_stimulus",
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
