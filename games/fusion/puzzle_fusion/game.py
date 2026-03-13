from core.game_contract import GameDescriptor
from games.common.binocular_fusion.scene import FusionGameConfig, FusionTrainingScene

CONFIG = FusionGameConfig(
    game_id="fusion.puzzle_fusion",
    category="fusion",
    name="Puzzle Fusion",
    name_key="game.fusion.puzzle_fusion",
    title_key="puzzle_fusion.title",
    subtitle_key="puzzle_fusion.subtitle",
    guide_key="puzzle_fusion.play.guide",
    metric_label_key="puzzle_fusion.metric.label",
    help_steps=("puzzle_fusion.help.step1", "puzzle_fusion.help.step2", "puzzle_fusion.help.step3"),
    mechanic_type="puzzle_fusion",
    theme_color=(120, 136, 226),
)


def create_scene(manager):
    return FusionTrainingScene(manager, CONFIG)


def build_descriptor():
    return GameDescriptor(
        game_id=CONFIG.game_id,
        category=CONFIG.category,
        name=CONFIG.name,
        factory=create_scene,
        name_key=CONFIG.name_key,
    )
