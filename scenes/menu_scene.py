import pygame
import sys
from core.base_scene import BaseScene
from config import SCREEN_WIDTH, SCREEN_HEIGHT


class MenuScene(BaseScene):

    def __init__(self, manager):
        super().__init__(manager)
        self._refresh_fonts()
        
        # 菜单卡片布局
        self.menu_width = 420
        self.menu_height = 58
        self.menu_gap = 18
        start_y = 260
        start_x = SCREEN_WIDTH // 2 - self.menu_width // 2

        self.menu_options = [
            {"rect": pygame.Rect(start_x, start_y + 0 * (self.menu_height + self.menu_gap), self.menu_width, self.menu_height), "key": "menu.start_training", "scene": "training"},
            {"rect": pygame.Rect(start_x, start_y + 1 * (self.menu_height + self.menu_gap), self.menu_width, self.menu_height), "key": "menu.configuration", "scene": "config"},
            {"rect": pygame.Rect(start_x, start_y + 2 * (self.menu_height + self.menu_gap), self.menu_width, self.menu_height), "key": "menu.view_history", "scene": "history"},
            {"rect": pygame.Rect(start_x, start_y + 3 * (self.menu_height + self.menu_gap), self.menu_width, self.menu_height), "key": "menu.exit", "scene": "exit"}
        ]

    def _refresh_fonts(self):
        self.title_font = self.create_font(62)
        self.subtitle_font = self.create_font(24)
        self.option_font = self.create_font(30)
        self.hint_font = self.create_font(20)

    def _draw_background(self, screen):
        # 深色渐变背景
        top = (17, 28, 48)
        bottom = (9, 14, 28)
        for y in range(SCREEN_HEIGHT):
            t = y / max(SCREEN_HEIGHT - 1, 1)
            color = (
                int(top[0] * (1 - t) + bottom[0] * t),
                int(top[1] * (1 - t) + bottom[1] * t),
                int(top[2] * (1 - t) + bottom[2] * t),
            )
            pygame.draw.line(screen, color, (0, y), (SCREEN_WIDTH, y))

        # 光晕层
        glow = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        pygame.draw.circle(glow, (70, 110, 180, 70), (SCREEN_WIDTH // 2, 170), 220)
        pygame.draw.circle(glow, (120, 160, 220, 35), (SCREEN_WIDTH // 2, 170), 150)
        screen.blit(glow, (0, 0))

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
                    sys.exit()
            
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:  # 左键点击
                    for option in self.menu_options:
                        if option["rect"].collidepoint(mouse_pos):
                            if option["scene"] == "exit":
                                pygame.quit()
                                sys.exit()
                            else:
                                self.manager.set_scene(option["scene"])

    def draw(self, screen):
        self._refresh_fonts()
        self._draw_background(screen)
        
        # 标题与副标题
        title = self.title_font.render(self.manager.t("menu.title"), True, (255, 255, 255))
        title_x = SCREEN_WIDTH // 2 - title.get_width() // 2
        screen.blit(title, (title_x, 100))

        subtitle = self.subtitle_font.render(self.manager.t("menu.subtitle"), True, (170, 195, 235))
        screen.blit(subtitle, (SCREEN_WIDTH // 2 - subtitle.get_width() // 2, 170))
        
        # 获取鼠标位置用于悬停检测
        mouse_pos = pygame.mouse.get_pos()
        
        # 绘制菜单项卡片
        for index, option in enumerate(self.menu_options, start=1):
            rect = option["rect"]
            text = f"{index}. {self.manager.t(option['key'])}"
            is_hovered = rect.collidepoint(mouse_pos)
            
            if is_hovered:
                text_color = (255, 255, 255)
                bg_color = (55, 84, 138)
                border_color = (170, 205, 255)
                accent_color = (140, 205, 255)
            else:
                text_color = (215, 225, 240)
                bg_color = (36, 52, 84)
                border_color = (92, 124, 180)
                accent_color = (72, 102, 160)

            pygame.draw.rect(screen, bg_color, rect, border_radius=10)
            pygame.draw.rect(screen, border_color, rect, 2, border_radius=10)

            # 左侧强调条
            accent_rect = pygame.Rect(rect.x + 8, rect.y + 8, 6, rect.height - 16)
            pygame.draw.rect(screen, accent_color, accent_rect, border_radius=4)
            
            # 绘制文字
            text_surface = self.option_font.render(text, True, text_color)
            text_x = rect.x + 28
            text_y = rect.centery - text_surface.get_height() // 2
            screen.blit(text_surface, (text_x, text_y))

        # 底部快捷键提示
        hint = self.hint_font.render(self.manager.t("menu.hint"), True, (150, 170, 205))
        screen.blit(hint, (SCREEN_WIDTH // 2 - hint.get_width() // 2, SCREEN_HEIGHT - 40))
