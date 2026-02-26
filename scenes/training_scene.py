import pygame
import random
import time
from core.base_scene import BaseScene
from core.e_generator import EGenerator
from config import E_SIZE_LEVELS


class Particle:
    """粒子效果类 - 用于显示✓和✗反馈"""
    
    def __init__(self, x, y, is_correct):
        self.x = x
        self.y = y
        self.is_correct = is_correct
        self.size = 40
        self.lifetime = 60  # 60帧后消失
        self.font = pygame.font.SysFont(None, self.size)
        self.create_surface()
        
    def create_surface(self):
        """创建粒子表面"""
        color = (0, 255, 0) if self.is_correct else (255, 0, 0)  # 绿色V或红色X
        text = "V" if self.is_correct else "X"  # 使用ASCII字符确保兼容性
        self.text_surface = self.font.render(text, True, color)
        
    def update(self):
        """更新粒子状态"""
        self.lifetime -= 1
        # 轻微上移动画效果
        self.y -= 1
        
    def draw(self, screen):
        """绘制粒子 - 使用颜色亮度调整替代透明度"""
        if self.lifetime <= 0:
            return
            
        # 计算亮度因子（通过lifetime控制）
        brightness_factor = self.lifetime / 60
        
        # 根据正确/错误获取基础颜色
        if self.is_correct:
            base_color = (0, 255, 0)  # 绿色
        else:
            base_color = (255, 0, 0)  # 红色
            
        # 调整颜色亮度（模拟淡出效果）
        adjusted_color = (
            int(base_color[0] * brightness_factor),
            int(base_color[1] * brightness_factor),
            int(base_color[2] * brightness_factor)
        )
        
        # 重新渲染文本表面 - 使用ASCII字符确保兼容性
        text = "V" if self.is_correct else "X"
        text_surface = self.font.render(text, True, adjusted_color)
        
        screen.blit(text_surface, (self.x - text_surface.get_width() // 2, 
                                 self.y - text_surface.get_height() // 2))
        
    def is_alive(self):
        """检查粒子是否还存活"""
        return self.lifetime > 0


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
        
        # 粒子效果列表
        self.particles = []

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
                    is_correct = (self.KEY_DIRECTION[event.key] == self.target_direction)
                    
                    # 创建粒子效果
                    particle_x = self.rect.centerx
                    particle_y = self.rect.centery - 50  # 在E字上方显示
                    self.particles.append(Particle(particle_x, particle_y, is_correct))
                    
                    # 播放音效反馈
                    if self.manager.sound_manager:
                        if is_correct:
                            self.manager.sound_manager.play_correct()
                        else:
                            self.manager.sound_manager.play_wrong()

                    if is_correct:
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
        
        # 更新和绘制粒子效果
        # 先更新所有粒子
        for particle in self.particles[:]:
            particle.update()
            if not particle.is_alive():
                self.particles.remove(particle)
        
        # 绘制所有存活的粒子
        for particle in self.particles:
            particle.draw(screen)
        
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