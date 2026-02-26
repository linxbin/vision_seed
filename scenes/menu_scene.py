import pygame
from core.base_scene import BaseScene


class MenuScene(BaseScene):

    def __init__(self, manager):
        super().__init__(manager)
        self.title_font = pygame.font.SysFont(None, 60)
        self.option_font = pygame.font.SysFont(None, 40)
        
        # 定义菜单选项的矩形区域（像素级精确位置）
        self.menu_options = [
            {"rect": pygame.Rect(320, 300, 280, 40), "text": "1. Start Training", "scene": "training"},
            {"rect": pygame.Rect(320, 350, 280, 40), "text": "2. Configuration", "scene": "config"},
            {"rect": pygame.Rect(320, 400, 280, 40), "text": "3. View History", "scene": "history"},
            {"rect": pygame.Rect(320, 450, 280, 40), "text": "4. Exit", "scene": "exit"}
        ]

    def handle_events(self, events):
        mouse_pos = pygame.mouse.get_pos()
        
        for event in events:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_1:
                    self.manager.set_scene("training")
                elif event.key == pygame.K_2:
                    self.manager.set_scene("config")
                elif event.key == pygame.K_3:
                    self.manager.set_scene("history")
                elif event.key == pygame.K_4:
                    pygame.quit()
                    exit()
            
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:  # 左键点击
                    for option in self.menu_options:
                        if option["rect"].collidepoint(mouse_pos):
                            if option["scene"] == "exit":
                                pygame.quit()
                                exit()
                            else:
                                self.manager.set_scene(option["scene"])

    def draw(self, screen):
        screen.fill((20, 20, 40))
        
        # 绘制标题（居中对齐）
        title = self.title_font.render("VisionSeed", True, (255, 255, 255))
        title_x = 450 - title.get_width() // 2  # 900/2 = 450
        screen.blit(title, (title_x, 150))
        
        # 获取鼠标位置用于悬停检测
        mouse_pos = pygame.mouse.get_pos()
        
        # 绘制菜单选项（带鼠标交互效果）
        for option in self.menu_options:
            rect = option["rect"]
            text = option["text"]
            is_hovered = rect.collidepoint(mouse_pos)
            
            # 颜色配置（符合强迫症的色彩规范）
            if is_hovered:
                text_color = (255, 255, 255)  # 悬停时白色
                bg_color = (40, 60, 100)      # 悬停背景色
            else:
                text_color = (200, 200, 200)  # 默认灰色
                bg_color = None               # 无背景色
            
            # 绘制悬停背景（仅在悬停时显示）
            if is_hovered:
                pygame.draw.rect(screen, bg_color, rect, border_radius=8)
                pygame.draw.rect(screen, (80, 120, 200), rect, 2, border_radius=8)
            
            # 绘制文字
            text_surface = self.option_font.render(text, True, text_color)
            text_x = rect.centerx - text_surface.get_width() // 2
            text_y = rect.centery - text_surface.get_height() // 2
            screen.blit(text_surface, (text_x, text_y))