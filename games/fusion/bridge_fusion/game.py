from core.game_contract import GameDescriptor
from games.common.binocular_fusion.scene import FusionGameConfig, FusionTrainingScene

CONFIG = FusionGameConfig(
    game_id="fusion.bridge_fusion",
    category="fusion",
    name="Bridge Fusion",
    name_key="game.fusion.bridge_fusion",
    title_key="bridge_fusion.title",
    subtitle_key="bridge_fusion.subtitle",
    guide_key="bridge_fusion.play.guide",
    metric_label_key="bridge_fusion.metric.label",
    help_steps=("bridge_fusion.help.step1", "bridge_fusion.help.step2", "bridge_fusion.help.step3"),
    mechanic_type="bridge_fusion",
    theme_color=(96, 168, 188),
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
