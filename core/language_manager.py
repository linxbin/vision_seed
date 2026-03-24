import logging

from games.accommodation.catch_fruit.i18n import TRANSLATIONS as CATCH_FRUIT_TRANSLATIONS
from games.accommodation.e_orientation.i18n import TRANSLATIONS as E_ORIENTATION_TRANSLATIONS
from games.accommodation.snake.i18n import TRANSLATIONS as SNAKE_TRANSLATIONS
from games.amblyopia.precision_aim.i18n import TRANSLATIONS as PRECISION_AIM_TRANSLATIONS
from games.amblyopia.fruit_slice.i18n import TRANSLATIONS as FRUIT_SLICE_TRANSLATIONS
from games.amblyopia.whack_a_mole.i18n import TRANSLATIONS as WHACK_A_MOLE_TRANSLATIONS
from games.common.training_runtime.i18n import TRANSLATIONS as ARCADE_TRANSLATIONS
from games.fusion.push_box.i18n import TRANSLATIONS as FUSION_PUSH_BOX_TRANSLATIONS
from games.fusion.path_fusion.i18n import TRANSLATIONS as PATH_FUSION_TRANSLATIONS
from games.fusion.tetris.i18n import TRANSLATIONS as TETRIS_TRANSLATIONS
from games.simultaneous.eye_find_patterns.i18n import TRANSLATIONS as EYE_FIND_TRANSLATIONS
from games.simultaneous.pong.i18n import TRANSLATIONS as PONG_TRANSLATIONS
from games.simultaneous.spot_difference.i18n import TRANSLATIONS as SPOT_DIFFERENCE_TRANSLATIONS
from games.stereopsis.depth_grab.i18n import TRANSLATIONS as DEPTH_GRAB_TRANSLATIONS
from games.stereopsis.pop_nearest.i18n import TRANSLATIONS as POP_NEAREST_TRANSLATIONS
from games.stereopsis.ring_flight.i18n import TRANSLATIONS as RING_FLIGHT_TRANSLATIONS
from games.suppression.find_same.i18n import TRANSLATIONS as FIND_SAME_TRANSLATIONS
from games.suppression.red_blue_catch.i18n import TRANSLATIONS as RED_BLUE_CATCH_TRANSLATIONS
from games.suppression.weak_eye_key.i18n import TRANSLATIONS as WEAK_EYE_KEY_TRANSLATIONS
from .metric_i18n import TRANSLATIONS as METRIC_TRANSLATIONS


logger = logging.getLogger(__name__)


def _merge_translations(*translation_sets):
    merged = {}
    for translation_set in translation_sets:
        for language, values in translation_set.items():
            merged.setdefault(language, {}).update(values)
    return merged


class LanguageManager:
    """Manages the current language and text translations."""

    DEFAULT_LANGUAGE = "en-US"
    SUPPORTED_LANGUAGES = ("en-US", "zh-CN")
    _warned_missing_keys = set()

    CORE_TRANSLATIONS = {
        "en-US": {
            "menu.title": "VisionSeed",
            "menu.subtitle": "Visual Training System",
            "menu.start_training": "Start Training",
            "menu.system_settings": "System Settings",
            "menu.configuration": "Configuration",
            "menu.view_history": "View History",
            "menu.exit": "Exit",
            "menu.hint": "Shortcuts: 1-9",
            "menu.recommend.title": "Today's Recommended Order",
            "menu.recommend.fresh": "fresh today",
            "menu.recommend.review": "review ({accuracy}%)",
            "menu.recommend.none": "Complete a training to see tailored suggestions.",
            "menu.recommend.start_fresh": "Start with fresh categories, then review today's weaker area.",
            "menu.recommend.review_focus": "Review {category} first today.",
            "menu.recent.title": "Recent",
            "menu.recent.item": "{game} ({accuracy}%)",
            "menu.recent.none": "No session yet",
            "menu.multigame_subtitle": "Multi-Game Training",
            "menu.template_title": "Quick Plans",
            "menu.template_child": "Child Plan",
            "menu.template_adult": "Adult Plan",
            "menu.template_recovery": "Recovery Plan",
            "onboarding.title": "30s Quick Start",
            "onboarding.subtitle": "Finish this once before your first training session",
            "onboarding.tip1": "Sit upright, keep a stable viewing distance, and avoid glare.",
            "onboarding.tip2": "Use arrow keys to answer E direction (Up/Down/Left/Right).",
            "onboarding.tip3": "Train 5-10 minutes per session, 1-2 sessions per day.",
            "onboarding.tip4": "This app is a training aid, not a medical diagnosis/treatment.",
            "onboarding.estimate": "Recommended start: L4 / 20-30 questions / steady pace",
            "onboarding.start": "I Understand",
            "onboarding.skip": "Skip",
            "license.title": "License Activation",
            "license.subtitle": "Send your device hash to seller for a device-bound token",
            "license.device_hash": "Device Hash",
            "license.copy_hash": "Copy Hash",
            "license.paste": "Paste",
            "license.paste_tip": "Tip: click Paste or press Ctrl+V",
            "license.input_placeholder": "Paste activation token (VS1....)",
            "license.activate": "Activate",
            "license.exit": "Exit",
            "license.hint": "C: Copy Hash  Enter: Activate  Esc: Exit",
            "license.success": "Activation succeeded.",
            "license.copy_success": "Device hash copied.",
            "license.copy_failed": "Copy failed. Please copy manually.",
            "license.paste_success": "Token pasted.",
            "license.paste_failed": "Paste failed. Please input manually.",
            "license.error_empty": "Please paste activation token.",
            "license.error_invalid": "Activation failed",
            "license.err.ERR_FORMAT": "Token format is invalid.",
            "license.err.ERR_PREFIX": "Token prefix is invalid.",
            "license.err.ERR_PAYLOAD": "Token payload is corrupted.",
            "license.err.ERR_SIGNATURE": "Token signature check failed.",
            "license.err.ERR_STATUS": "License status is not active.",
            "license.err.ERR_SCHEMA": "License version is unsupported.",
            "license.err.ERR_DEVICE": "This token does not match this device.",
            "license.err.ERR_EXPIRED": "License has expired.",
            "license.err.ERR_WRITE": "Local license file write failed.",
            "license.err.ERR_NOT_FOUND": "License file not found.",
            "license.err.ERR_UNREADABLE": "License file is unreadable.",
            "license.err.OK": "OK",
            "config.on": "ON",
            "config.off": "OFF",
            "config.lang_en": "English",
            "config.lang_zh": "Chinese",
            "common.back": "Back",
            "system.title": "System Settings",
            "system.hint": "1: Toggle Sound  2: Toggle Language  3: Session Time  Esc: Back",
            "system.sound": "Sound: {value}",
            "system.language": "Language: {value}",
            "system.duration": "Session Duration: {value}",
            "system.duration_value": "{n} min",
            "category.accommodation": "Accommodation Training",
            "category.simultaneous": "Simultaneous Vision Training",
            "category.fusion": "Fusion Training",
            "category.suppression": "Suppression Release Training",
            "category.stereopsis": "Stereopsis Training",
            "category.amblyopia": "Amblyopia Training",
            "category.unknown": "Category",
            "category.empty": "No games in this category",
            "category.hint": "Esc or Back: Return",
            "category.latest_summary": "Latest: {accuracy}% / {duration}s",
            "category.latest_metric": "{label}: {value}",
        },
        "zh-CN": {
            "menu.title": "视觉芽",
            "menu.subtitle": "视觉训练系统",
            "menu.start_training": "开始训练",
            "menu.system_settings": "系统设置",
            "menu.configuration": "参数配置",
            "menu.view_history": "训练历史",
            "menu.exit": "退出",
            "menu.hint": "快捷键：1-9",
            "menu.recommend.title": "今日推荐训练顺序",
            "menu.recommend.fresh": "今天优先开始",
            "menu.recommend.review": "建议复习（{accuracy}%）",
            "menu.recommend.none": "完成一次训练后，这里会显示个性化建议。",
            "menu.recommend.start_fresh": "建议先练今天还没覆盖的分类，再回看较弱项。",
            "menu.recommend.review_focus": "今天建议先复习 {category}。",
            "menu.recent.title": "最近完成",
            "menu.recent.item": "{game}（{accuracy}%）",
            "menu.recent.none": "还没有训练记录",
            "menu.multigame_subtitle": "多游戏训练系统",
            "menu.template_title": "快捷训练方案",
            "menu.template_child": "儿童方案",
            "menu.template_adult": "成人方案",
            "menu.template_recovery": "恢复方案",
            "onboarding.title": "30秒快速上手",
            "onboarding.subtitle": "首次使用建议先完成一次引导",
            "onboarding.tip1": "坐姿端正，保持稳定训练距离，避免环境眩光。",
            "onboarding.tip2": "使用方向键判断 E 方向（上/下/左/右）。",
            "onboarding.tip3": "每次训练 5-10 分钟，每日 1-2 次。",
            "onboarding.tip4": "本软件为训练辅助工具，不替代医疗诊断与治疗。",
            "onboarding.estimate": "建议起步：L4 / 20-30题 / 匀速完成",
            "onboarding.start": "我已了解",
            "onboarding.skip": "跳过",
            "license.title": "授权激活",
            "license.subtitle": "请将设备哈希发给卖家，获取绑定本机的授权码",
            "license.device_hash": "设备哈希",
            "license.copy_hash": "复制哈希",
            "license.paste": "粘贴",
            "license.paste_tip": "提示：可点击“粘贴”或按 Ctrl+V",
            "license.input_placeholder": "请粘贴授权码（VS1....）",
            "license.activate": "激活",
            "license.exit": "退出",
            "license.hint": "C: 复制哈希  回车: 激活  Esc: 退出",
            "license.success": "激活成功。",
            "license.copy_success": "设备哈希已复制。",
            "license.copy_failed": "复制失败，请手动抄录。",
            "license.paste_success": "授权码已粘贴。",
            "license.paste_failed": "粘贴失败，请手动输入。",
            "license.error_empty": "请先输入授权码。",
            "license.error_invalid": "激活失败",
            "license.err.ERR_FORMAT": "授权码格式错误。",
            "license.err.ERR_PREFIX": "授权码前缀无效。",
            "license.err.ERR_PAYLOAD": "授权码内容损坏。",
            "license.err.ERR_SIGNATURE": "授权码签名校验失败。",
            "license.err.ERR_STATUS": "授权状态不是可用状态。",
            "license.err.ERR_SCHEMA": "授权版本不受支持。",
            "license.err.ERR_DEVICE": "授权码与当前设备不匹配。",
            "license.err.ERR_EXPIRED": "授权已过期。",
            "license.err.ERR_WRITE": "本地授权文件写入失败。",
            "license.err.ERR_NOT_FOUND": "未找到本地授权文件。",
            "license.err.ERR_UNREADABLE": "本地授权文件损坏。",
            "license.err.OK": "正常",
            "config.on": "开",
            "config.off": "关",
            "config.lang_en": "英文",
            "config.lang_zh": "中文",
            "common.back": "返回",
            "system.title": "系统设置",
            "system.hint": "1：切换音效  2：切换语言  3：每局时长  Esc：返回",
            "system.sound": "音效：{value}",
            "system.language": "语言：{value}",
            "system.duration": "每局时长：{value}",
            "system.duration_value": "{n}分钟",
            "category.accommodation": "调节训练",
            "category.simultaneous": "同时视训练",
            "category.fusion": "融合视训练",
            "category.suppression": "脱抑制训练",
            "category.stereopsis": "立体视训练",
            "category.amblyopia": "弱视训练",
            "category.unknown": "分类",
            "category.empty": "该分类暂无游戏",
            "category.hint": "Esc 或 返回：回到主菜单",
            "category.latest_summary": "最近一次：正确率{accuracy}% / {duration}秒",
            "category.latest_metric": "{label}：{value}",
        },
    }

    TRANSLATIONS = _merge_translations(
        CORE_TRANSLATIONS,
        ARCADE_TRANSLATIONS,
        E_ORIENTATION_TRANSLATIONS,
        CATCH_FRUIT_TRANSLATIONS,
        SNAKE_TRANSLATIONS,
        TETRIS_TRANSLATIONS,
        PATH_FUSION_TRANSLATIONS,
        FUSION_PUSH_BOX_TRANSLATIONS,
        EYE_FIND_TRANSLATIONS,
        PONG_TRANSLATIONS,
        SPOT_DIFFERENCE_TRANSLATIONS,
        FIND_SAME_TRANSLATIONS,
        RED_BLUE_CATCH_TRANSLATIONS,
        WEAK_EYE_KEY_TRANSLATIONS,
        METRIC_TRANSLATIONS,
        DEPTH_GRAB_TRANSLATIONS,
        POP_NEAREST_TRANSLATIONS,
        RING_FLIGHT_TRANSLATIONS,
        PRECISION_AIM_TRANSLATIONS,
        FRUIT_SLICE_TRANSLATIONS,
        WHACK_A_MOLE_TRANSLATIONS,
    )

    def __init__(self, language=DEFAULT_LANGUAGE):
        self.current_language = self.DEFAULT_LANGUAGE
        self.set_language(language)

    def set_language(self, language):
        if language in self.SUPPORTED_LANGUAGES:
            self.current_language = language
        else:
            self.current_language = self.DEFAULT_LANGUAGE
        return self.current_language

    def cycle_language(self):
        if self.current_language == "en-US":
            self.current_language = "zh-CN"
        else:
            self.current_language = "en-US"
        return self.current_language

    def get_language(self):
        return self.current_language

    def t(self, key, **kwargs):
        language_map = self.TRANSLATIONS.get(self.current_language, {})
        fallback_map = self.TRANSLATIONS[self.DEFAULT_LANGUAGE]
        template = language_map.get(key, fallback_map.get(key))
        if template is None:
            warn_key = (self.current_language, key)
            if warn_key not in self._warned_missing_keys:
                logger.warning("Missing translation key for %s: %s", self.current_language, key)
                self._warned_missing_keys.add(warn_key)
            template = key
        if kwargs:
            try:
                return template.format(**kwargs)
            except (KeyError, ValueError):
                return template
        return template
