from config import DEFAULT_TOTAL_QUESTIONS, DEFAULT_START_LEVEL
from .sound_manager import SoundManager
from .data_manager import DataManager
from .preferences_manager import PreferencesManager
from .language_manager import LanguageManager
from .license_manager import LicenseManager


class SceneManager:
    def __init__(self):
        self.scene = None
        self.scenes = {}
        self.screen_size = None

        self.settings = {
            "total_questions": DEFAULT_TOTAL_QUESTIONS,
            "start_level": DEFAULT_START_LEVEL,
            "sound_enabled": True,
            "language": "en-US",
            "fullscreen": False,
            "onboarding_completed": False,
        }

        # 用户偏好管理器
        self.preferences_manager = PreferencesManager()
        self.settings.update(self.preferences_manager.load_preferences())
        self.language_manager = LanguageManager(self.settings.get("language", "en-US"))
        self.settings["language"] = self.language_manager.get_language()

        # ⭐ 当前训练结果统一存储
        self.current_result = {
            "correct": 0,
            "total": 0
        }
        
        # 音效管理器
        self.sound_manager = SoundManager()
        self.apply_sound_preference()
        
        # 数据管理器
        self.data_manager = DataManager()
        self.license_manager = LicenseManager()

    def apply_sound_preference(self):
        """将当前偏好中的音效开关应用到音效管理器。"""
        if self.sound_manager:
            self.sound_manager.set_enabled(self.settings.get("sound_enabled", True))

    def apply_language_preference(self):
        """将当前偏好中的语言应用到语言管理器。"""
        self.settings["language"] = self.language_manager.set_language(
            self.settings.get("language", "en-US")
        )

    def t(self, key, **kwargs):
        """文案翻译快捷方法。"""
        return self.language_manager.t(key, **kwargs)

    def save_user_preferences(self) -> bool:
        """保存当前用户偏好设置。"""
        payload = {
            "start_level": self.settings["start_level"],
            "total_questions": self.settings["total_questions"],
            "sound_enabled": self.settings.get("sound_enabled", True),
            "language": self.settings.get("language", "en-US"),
            "fullscreen": self.settings.get("fullscreen", False),
            "onboarding_completed": self.settings.get("onboarding_completed", False),
        }
        return self.preferences_manager.save_preferences(payload)

    def apply_training_template(self, template_id: str):
        templates = {
            "child": {"start_level": 6, "total_questions": 20},
            "adult": {"start_level": 4, "total_questions": 30},
            "recovery": {"start_level": 7, "total_questions": 12},
        }
        selected = templates.get(template_id)
        if not selected:
            return
        self.settings["start_level"] = selected["start_level"]
        self.settings["total_questions"] = selected["total_questions"]
        self.save_user_preferences()

    def register(self, name, scene):
        self.scenes[name] = scene

    def set_screen_size(self, width, height):
        self.screen_size = (width, height)

    def set_scene(self, name):
        self.scene = self.scenes[name]

        if self.screen_size:
            on_resize = getattr(self.scene, "on_resize", None)
            if callable(on_resize):
                on_resize(*self.screen_size)

        # 每次进入训练必须重置
        if name == "training":
            self.scene.reset()
            return

        # 场景进入回调（可选）
        on_enter = getattr(self.scene, "on_enter", None)
        if callable(on_enter):
            on_enter()

    def get_scene(self):
        return self.scene
