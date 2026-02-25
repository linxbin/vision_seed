import pygame
import random
import time
from core.base_scene import BaseScene
from core.e_generator import EGenerator
from config import E_SIZE_LEVELS


class TrainingScene(BaseScene):

    KEY_DIRECTION = {
        pygame.K_UP: "UP",
        pygame.K_DOWN: "DOWN",
        pygame.K_LEFT: "LEFT",
        pygame.K_RIGHT: "RIGHT"
    }

    def __init__(self, manager):
        super().__init__(manager)
        self.reset()

    def reset(self):
        self.total = self.manager.settings["total_questions"]
        self.current = 0
        self.correct = 0
        self.start_time = time.time()
        self.previous_direction = None
        
        # 根据设置的难度等级获取对应的E字大小
        # start_level范围是1-7，对应E_SIZE_LEVELS索引0-6
        level_index = self.manager.settings["start_level"] - 1
        self.base_size = E_SIZE_LEVELS[level_index]
        
        self.new_question()

    def new_question(self):

        directions = ["UP", "DOWN", "LEFT", "RIGHT"]

        if self.previous_direction in directions:
            directions.remove(self.previous_direction)

        self.target_direction = random.choice(directions)
        self.previous_direction = self.target_direction

        self.surface = EGenerator.create_e_surface(self.base_size, self.target_direction)
        self.rect = self.surface.get_rect(center=(450, 300))

    def handle_events(self, events):
        for event in events:
            if event.type == pygame.KEYDOWN:

                if event.key == pygame.K_ESCAPE:
                    self.manager.set_scene("menu")

                if event.key in self.KEY_DIRECTION:

                    self.current += 1

                    if self.KEY_DIRECTION[event.key] == self.target_direction:
                        self.correct += 1

                    if self.current >= self.total:

                        duration = round(time.time() - self.start_time, 2)
                        wrong = self.total - self.correct

                        self.manager.current_result["correct"] = self.correct
                        self.manager.current_result["wrong"] = wrong
                        self.manager.current_result["total"] = self.total
                        self.manager.current_result["duration"] = duration

                        self.manager.set_scene("report")
                    else:
                        self.new_question()

    def draw(self, screen):
        screen.fill((0, 0, 0))
        screen.blit(self.surface, self.rect)

        small = pygame.font.SysFont(None, 40)
        progress = f"{self.current}/{self.total}"
        screen.blit(small.render(progress, True, (200, 200, 200)), (420, 620))