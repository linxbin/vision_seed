import pygame
from core.base_scene import BaseScene


class ReportScene(BaseScene):

    def __init__(self, manager):
        super().__init__(manager)
        self.font = pygame.font.SysFont(None, 60)
        self.small = pygame.font.SysFont(None, 48)

    def handle_events(self, events):
        for event in events:
            if event.type == pygame.KEYDOWN:
                self.manager.set_scene("menu")

    def draw(self, screen):
        screen.fill((20, 50, 20))

        correct = self.manager.current_result["correct"]
        wrong = self.manager.current_result["wrong"]
        total = self.manager.current_result["total"]
        duration = self.manager.current_result["duration"]

        screen.blit(self.font.render("Training Report", True, (255, 255, 255)), (300, 150))

        screen.blit(self.small.render(f"Total Questions: {total}", True, (255, 255, 255)), (300, 260))
        screen.blit(self.small.render(f"Correct: {correct}", True, (255, 255, 255)), (300, 320))
        screen.blit(self.small.render(f"Wrong: {wrong}", True, (255, 255, 255)), (300, 380))
        screen.blit(self.small.render(f"Time Used: {duration} s", True, (255, 255, 255)), (300, 440))

        screen.blit(self.small.render("Press any key to return", True, (200, 200, 200)), (250, 550))