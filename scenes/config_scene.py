import pygame
from core.base_scene import BaseScene
from core.e_generator import EGenerator
from config import E_SIZE_LEVELS, SCREEN_WIDTH, SCREEN_HEIGHT


class ConfigScene(BaseScene):
    """配置场景 - 用于设置难度等级"""

    def __init__(self, manager):
        super().__init__(manager)
        self.font = pygame.font.SysFont(None, 32)
        self.title_font = pygame.font.SysFont(None, 48)
        self.e_generator = EGenerator()
        
        # 初始化当前选中的等级（从settings中读取）
        self.current_level = self.manager.settings["start_level"]

    def handle_events(self, events):
        for event in events:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    # 返回菜单前保存设置
                    self.manager.settings["start_level"] = self.current_level
                    self.manager.set_scene("menu")
                elif event.key == pygame.K_RETURN:
                    # 确认设置并开始训练
                    self.manager.settings["start_level"] = self.current_level
                    self.manager.set_scene("training")
                elif event.key == pygame.K_UP:
                    # 向上选择更高等级（更大字体）
                    self.current_level = min(8, self.current_level + 1)
                elif event.key == pygame.K_DOWN:
                    # 向下选择更低等级（更小字体）
                    self.current_level = max(1, self.current_level - 1)
                elif event.key in [pygame.K_1, pygame.K_2, pygame.K_3, pygame.K_4, 
                                 pygame.K_5, pygame.K_6, pygame.K_7, pygame.K_8]:
                    # 直接选择等级1-8
                    level_map = {
                        pygame.K_1: 1, pygame.K_2: 2, pygame.K_3: 3, pygame.K_4: 4,
                        pygame.K_5: 5, pygame.K_6: 6, pygame.K_7: 7, pygame.K_8: 8
                    }
                    self.current_level = level_map[event.key]

    def draw(self, screen):
        screen.fill((30, 30, 50))
        
        # 绘制标题
        title = self.title_font.render("Select Difficulty Level", True, (255, 255, 255))
        screen.blit(title, (SCREEN_WIDTH // 2 - title.get_width() // 2, 50))
        
        # 绘制等级说明
        info_text = self.font.render("↑↓: Navigate  Enter: Start  ESC: Back", True, (200, 200, 200))
        screen.blit(info_text, (SCREEN_WIDTH // 2 - info_text.get_width() // 2, 120))
        
        # 左侧：等级按钮列表
        button_start_y = 200
        button_height = 45
        button_width = 200
        
        for i in range(8):
            level = i + 1
            y_pos = button_start_y + i * (button_height + 10)
            
            # 按钮背景
            button_color = (80, 120, 200) if level == self.current_level else (60, 60, 90)
            pygame.draw.rect(screen, button_color, (100, y_pos, button_width, button_height))
            pygame.draw.rect(screen, (150, 180, 255) if level == self.current_level else (100, 100, 150), 
                           (100, y_pos, button_width, button_height), 2)
            
            # 按钮文字
            level_text = f"Level {level}"
            size_text = f"({E_SIZE_LEVELS[i]}px)"
            full_text = f"{level_text} {size_text}"
            text_surface = self.font.render(full_text, True, (255, 255, 255))
            screen.blit(text_surface, (100 + button_width // 2 - text_surface.get_width() // 2, 
                                     y_pos + button_height // 2 - text_surface.get_height() // 2))
        
        # 右侧：当前等级E字预览
        preview_center = (SCREEN_WIDTH - 200, SCREEN_HEIGHT // 2)
        current_size = E_SIZE_LEVELS[self.current_level - 1]
        
        # 绘制预览框
        preview_size = current_size + 40
        pygame.draw.rect(screen, (50, 50, 80), 
                        (preview_center[0] - preview_size//2, 
                         preview_center[1] - preview_size//2, 
                         preview_size, preview_size))
        pygame.draw.rect(screen, (100, 100, 150), 
                        (preview_center[0] - preview_size//2, 
                         preview_center[1] - preview_size//2, 
                         preview_size, preview_size), 2)
        
        # 绘制E字预览
        self.e_generator.draw_e(screen, preview_center, current_size, "RIGHT")
        
        # 预览标题
        preview_title = self.font.render(f"Preview - Level {self.current_level}", True, (255, 255, 255))
        screen.blit(preview_title, (SCREEN_WIDTH - 200 - preview_title.get_width() // 2, 
                                   SCREEN_HEIGHT // 2 - preview_size // 2 - 30))
        
        # 当前选中提示
        selected_text = self.font.render(f"Selected: Level {self.current_level} ({current_size}px)", 
                                       True, (100, 200, 100))
        screen.blit(selected_text, (SCREEN_WIDTH // 2 - selected_text.get_width() // 2, 
                                  SCREEN_HEIGHT - 80))