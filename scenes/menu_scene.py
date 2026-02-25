import pygame
from core.base_scene import BaseScene


class MenuScene(BaseScene):

    def __init__(self, manager):
        super().__init__(manager)
        self.font = pygame.font.SysFont(None, 60)
        self.small = pygame.font.SysFont(None, 40)

    def handle_events(self, events):
        for event in events:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_1:
                    self.manager.set_scene("training")
                elif event.key == pygame.K_2:
                    self.manager.set_scene("config")  # 改为config场景
                elif event.key == pygame.K_3:
                    pygame.quit()
                    exit()

    def draw(self, screen):
        screen.fill((20, 20, 40))

        title = self.font.render("VisionSeed", True, (255, 255, 255))
        screen.blit(title, (320, 150))

        screen.blit(self.small.render("1. Start Training", True, (200, 200, 200)), (320, 300))
        screen.blit(self.small.render("2. Configuration", True, (200, 200, 200)), (320, 350))  # 改为Configuration
        screen.blit(self.small.render("3. Exit", True, (200, 200, 200)), (320, 400))