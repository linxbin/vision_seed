import pygame
from core.base_scene import BaseScene


class ReportScene(BaseScene):

    def __init__(self, manager):
        super().__init__(manager)
        self._refresh_fonts()

    def _refresh_fonts(self):
        self.font = self.create_font(60)
        self.small = self.create_font(48)

    def handle_events(self, events):
        for event in events:
            if event.type == pygame.KEYDOWN:
                self.manager.set_scene("menu")

    def draw(self, screen):
        self._refresh_fonts()
        screen.fill((20, 50, 20))

        correct = self.manager.current_result["correct"]
        wrong = self.manager.current_result["wrong"]
        total = self.manager.current_result["total"]
        duration = self.manager.current_result["duration"]

        screen.blit(self.font.render(self.manager.t("report.title"), True, (255, 255, 255)), (300, 150))

        screen.blit(self.small.render(self.manager.t("report.total_questions", total=total), True, (255, 255, 255)), (300, 260))
        screen.blit(self.small.render(self.manager.t("report.correct", correct=correct), True, (255, 255, 255)), (300, 320))
        screen.blit(self.small.render(self.manager.t("report.wrong", wrong=wrong), True, (255, 255, 255)), (300, 380))
        screen.blit(self.small.render(self.manager.t("report.time_used", duration=duration), True, (255, 255, 255)), (300, 440))

        screen.blit(self.small.render(self.manager.t("report.return_hint"), True, (200, 200, 200)), (250, 550))
