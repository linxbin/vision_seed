import pygame
from core.base_scene import BaseScene
from config import MIN_LEVEL, MAX_LEVEL, MIN_QUESTIONS, MAX_QUESTIONS


class SettingsScene(BaseScene):

    def __init__(self, manager):
        super().__init__(manager)
        self.font = pygame.font.SysFont(None, 48)

    def handle_events(self, events):
        for event in events:
            if event.type == pygame.KEYDOWN:

                if event.key == pygame.K_ESCAPE:
                    self.manager.set_scene("menu")

                elif event.key == pygame.K_LEFT:
                    self.manager.settings["total_questions"] = max(
                        MIN_QUESTIONS,
                        self.manager.settings["total_questions"] - 10
                    )

                elif event.key == pygame.K_RIGHT:
                    self.manager.settings["total_questions"] = min(
                        MAX_QUESTIONS,
                        self.manager.settings["total_questions"] + 10
                    )

                elif event.key == pygame.K_UP:
                    self.manager.settings["start_level"] = max(
                        MIN_LEVEL,
                        self.manager.settings["start_level"] - 1
                    )

                elif event.key == pygame.K_DOWN:
                    self.manager.settings["start_level"] = min(
                        MAX_LEVEL,
                        self.manager.settings["start_level"] + 1
                    )

    def draw(self, screen):
        screen.fill((30, 30, 50))

        screen.blit(self.font.render("Settings", True, (255, 255, 255)), (350, 150))

        screen.blit(self.font.render(
            f"Questions: {self.manager.settings['total_questions']} (← →)",
            True, (200, 200, 200)), (250, 300))

        screen.blit(self.font.render(
            f"Start Level: {self.manager.settings['start_level']} (↑ ↓)",
            True, (200, 200, 200)), (250, 360))