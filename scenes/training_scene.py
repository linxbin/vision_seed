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
        self.small_font = pygame.font.SysFont(None, 40)
        self.back_button_font = pygame.font.SysFont(None, 24)  # 专门为返回按钮创建合适大小的字体
        self.reset()
        
        # 返回按钮矩形（右上角，增大尺寸以容纳文字）
        self.back_button_rect = pygame.Rect(810, 15, 80, 30)

    def reset(self):
        self.total = self.manager.settings["total_questions"]
        self.current = 0
        self.correct = 0
        self.start_time = time.time()
        self.previous_direction = None
        
        # 根据设置的难度等级获取对应的E字大小
        # start_level范围是1-8，对应E_SIZE_LEVELS索引0-7
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
        mouse_pos = pygame.mouse.get_pos()
        
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
            
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:  # 左键点击
                    if self.back_button_rect.collidepoint(mouse_pos):
                        self.manager.set_scene("menu")

    def draw(self, screen):
        screen.fill((0, 0, 0))
        screen.blit(self.surface, self.rect)

        progress = f"{self.current}/{self.total}"
        screen.blit(self.small_font.render(progress, True, (200, 200, 200)), (420, 620))
        
        # 绘制返回按钮（右上角，强迫症级别的精确位置）
        mouse_pos = pygame.mouse.get_pos()
        is_hovered = self.back_button_rect.collidepoint(mouse_pos)
        
        # 按钮背景色
        button_color = (80, 120, 200) if is_hovered else (60, 90, 150)
        border_color = (150, 180, 255) if is_hovered else (100, 130, 200)
        
        pygame.draw.rect(screen, button_color, self.back_button_rect, border_radius=6)
        pygame.draw.rect(screen, border_color, self.back_button_rect, 2, border_radius=6)
        
        # 按钮文字（使用专门的字体大小，确保完美适配）
        back_text = self.back_button_font.render("Back", True, (255, 255, 255))
        text_x = self.back_button_rect.centerx - back_text.get_width() // 2
        text_y = self.back_button_rect.centery - back_text.get_height() // 2
        screen.blit(back_text, (text_x, text_y))