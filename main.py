import pygame
from config import SCREEN_WIDTH, SCREEN_HEIGHT, FPS, TITLE
from core.scene_manager import SceneManager
from scenes.menu_scene import MenuScene
from scenes.config_scene import ConfigScene  # 替换settings_scene
from scenes.training_scene import TrainingScene
from scenes.report_scene import ReportScene


def main():
    pygame.init()
    
    # 初始化音频混音器
    pygame.mixer.init(frequency=22050, size=-16, channels=2, buffer=512)
    
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption(TITLE)

    clock = pygame.time.Clock()

    manager = SceneManager()

    manager.register("menu", MenuScene(manager))
    manager.register("config", ConfigScene(manager))  # 使用config场景
    manager.register("training", TrainingScene(manager))
    manager.register("report", ReportScene(manager))

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