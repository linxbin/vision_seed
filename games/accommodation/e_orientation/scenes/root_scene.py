from core.base_scene import BaseScene

from .config_scene import ConfigScene
from .history_scene import HistoryScene
from .menu_scene import ETrainingMenuScene
from .report_scene import ReportScene
from .training_scene import TrainingScene


class _ETrainingManagerProxy:
    LOCAL_SCENES = {"menu", "config", "training", "history", "report", "game_host"}

    def __init__(self, root_scene):
        self._root_scene = root_scene

    def set_scene(self, name):
        if name in self.LOCAL_SCENES:
            target = "menu" if name == "game_host" else name
            self._root_scene.navigate(target)
            return
        self._root_scene.manager.set_scene(name)

    def __getattr__(self, name):
        return getattr(self._root_scene.manager, name)


class ETrainingRootScene(BaseScene):
    RESET_ON_ENTER = {"menu", "training"}

    def __init__(self, manager):
        super().__init__(manager)
        self.proxy = _ETrainingManagerProxy(self)
        self.child_scenes = {
            "menu": ETrainingMenuScene(self.proxy),
            "config": ConfigScene(self.proxy),
            "training": TrainingScene(self.proxy),
            "history": HistoryScene(self.proxy),
            "report": ReportScene(self.proxy),
        }
        self.current_scene_name = "menu"
        self.current_scene = self.child_scenes[self.current_scene_name]

    def _resize_child(self, scene):
        if self.manager.screen_size and hasattr(scene, "on_resize"):
            scene.on_resize(*self.manager.screen_size)

    def navigate(self, name, force_reset=False):
        scene = self.child_scenes.get(name)
        if scene is None:
            self.manager.set_scene(name)
            return
        self.current_scene_name = name
        self.current_scene = scene
        self._resize_child(scene)
        if force_reset or name in self.RESET_ON_ENTER:
            reset = getattr(scene, "reset", None)
            if callable(reset):
                reset()
                return
        on_enter = getattr(scene, "on_enter", None)
        if callable(on_enter):
            on_enter()

    def reset(self):
        self.navigate("menu", force_reset=True)

    def on_enter(self):
        self.navigate(self.current_scene_name, force_reset=False)

    def on_resize(self, width, height):
        if hasattr(self.current_scene, "on_resize"):
            self.current_scene.on_resize(width, height)

    def handle_events(self, events):
        self.current_scene.handle_events(events)

    def update(self):
        self.current_scene.update()

    def draw(self, screen):
        self.current_scene.draw(screen)
