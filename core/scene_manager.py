from config import DEFAULT_TOTAL_QUESTIONS, DEFAULT_START_LEVEL
from .sound_manager import SoundManager


class SceneManager:
    def __init__(self):
        self.scene = None
        self.scenes = {}

        self.settings = {
            "total_questions": DEFAULT_TOTAL_QUESTIONS,
            "start_level": DEFAULT_START_LEVEL
        }

        # ⭐ 当前训练结果统一存储
        self.current_result = {
            "correct": 0,
            "total": 0
        }
        
        # 音效管理器
        self.sound_manager = SoundManager()

    def register(self, name, scene):
        self.scenes[name] = scene

    def set_scene(self, name):
        self.scene = self.scenes[name]

        # 每次进入训练必须重置
        if name == "training":
            self.scene.reset()

    def get_scene(self):
        return self.scene