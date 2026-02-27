import pygame
from config import SCREEN_WIDTH, SCREEN_HEIGHT, FPS, TITLE
from core.scene_manager import SceneManager
from core.startup_health import run_startup_health_check, safe_init_audio
from scenes.menu_scene import MenuScene
from scenes.config_scene import ConfigScene
from scenes.training_scene import TrainingScene
from scenes.report_scene import ReportScene
from scenes.history_scene import HistoryScene

def main():
    pygame.init()

    run_startup_health_check()
    audio_ok = safe_init_audio()
    
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption(TITLE)

    clock = pygame.time.Clock()

    manager = SceneManager()
    if not audio_ok:
        manager.settings["sound_enabled"] = False
        manager.apply_sound_preference()

    manager.register("menu", MenuScene(manager))
    manager.register("config", ConfigScene(manager))
    manager.register("training", TrainingScene(manager))
    manager.register("report", ReportScene(manager))
    manager.register("history", HistoryScene(manager))

    manager.set_scene("menu")

    running = True
    while running:
        clock.tick(FPS)

        events = pygame.event.get()
        for event in events:
            if event.type == pygame.QUIT:
                running = False

        manager.get_scene().handle_events(events)
        manager.get_scene().update()
        manager.get_scene().draw(screen)

        pygame.display.flip()

    pygame.quit()


if __name__ == "__main__":
    main()
