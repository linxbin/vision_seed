import pygame
import sys
from core.base_scene import BaseScene
from config import SCREEN_WIDTH, SCREEN_HEIGHT


class MenuScene(BaseScene):

    def __init__(self, manager):
        super().__init__(manager)
        self._refresh_fonts()

        self.width = SCREEN_WIDTH
        self.height = SCREEN_HEIGHT

        # 菜单卡片布局
        self.menu_width = 420
        self.menu_height = 58
        self.menu_gap = 18
        self._reflow_layout()

    def _refresh_fonts(self):
        self.title_font = self.create_font(62)
        self.subtitle_font = self.create_font(24)
        self.option_font = self.create_font(30)
        self.hint_font = self.create_font(20)
        self.template_font = self.create_font(19)

    def _reflow_layout(self):
        self.top_offset = max(0, (self.height - SCREEN_HEIGHT) // 2)
        start_y = 220 + self.top_offset
        start_x = self.width // 2 - self.menu_width // 2

        self.menu_options = [
            {"rect": pygame.Rect(start_x, start_y + 0 * (self.menu_height + self.menu_gap), self.menu_width, self.menu_height), "key": "menu.start_training", "scene": "training"},
            {"rect": pygame.Rect(start_x, start_y + 1 * (self.menu_height + self.menu_gap), self.menu_width, self.menu_height), "key": "menu.configuration", "scene": "config"},
            {"rect": pygame.Rect(start_x, start_y + 2 * (self.menu_height + self.menu_gap), self.menu_width, self.menu_height), "key": "menu.view_history", "scene": "history"},
            {"rect": pygame.Rect(start_x, start_y + 3 * (self.menu_height + self.menu_gap), self.menu_width, self.menu_height), "key": "menu.exit", "scene": "exit"}
        ]
        template_y = start_y + 4 * (self.menu_height + self.menu_gap) + 36
        template_w = 132
        template_h = 70
        template_gap = 12
        template_start_x = self.width // 2 - (template_w * 3 + template_gap * 2) // 2
        self.templates = [
            {
                "rect": pygame.Rect(template_start_x, template_y, template_w, template_h),
                "key": "menu.template_child",
                "template_id": "child",
                "shortcut": pygame.K_5,
            },
            {
                "rect": pygame.Rect(template_start_x + template_w + template_gap, template_y, template_w, template_h),
                "key": "menu.template_adult",
                "template_id": "adult",
                "shortcut": pygame.K_6,
            },
            {
                "rect": pygame.Rect(template_start_x + (template_w + template_gap) * 2, template_y, template_w, template_h),
                "key": "menu.template_recovery",
                "template_id": "recovery",
                "shortcut": pygame.K_7,
            },
        ]

    def _start_with_template(self, template_id):
        self.manager.apply_training_template(template_id)
        self.manager.set_scene("training")

    def on_resize(self, width, height):
        self.width = width
        self.height = height
        self._reflow_layout()

    def _draw_background(self, screen):
        # 深色渐变背景
        top = (17, 28, 48)
        bottom = (9, 14, 28)
        for y in range(self.height):
            t = y / max(self.height - 1, 1)
            color = (
                int(top[0] * (1 - t) + bottom[0] * t),
                int(top[1] * (1 - t) + bottom[1] * t),
                int(top[2] * (1 - t) + bottom[2] * t),
            )
            pygame.draw.line(screen, color, (0, y), (self.width, y))

        # 光晕层
        glow = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        pygame.draw.circle(glow, (70, 110, 180, 70), (self.width // 2, 170 + self.top_offset), 220)
        pygame.draw.circle(glow, (120, 160, 220, 35), (self.width // 2, 170 + self.top_offset), 150)
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
                elif event.key == pygame.K_5:
                    self._start_with_template("child")
                elif event.key == pygame.K_6:
                    self._start_with_template("adult")
                elif event.key == pygame.K_7:
                    self._start_with_template("recovery")
            
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:  # 左键点击
                    for option in self.menu_options:
                        if option["rect"].collidepoint(mouse_pos):
                            if option["scene"] == "exit":
                                pygame.quit()
                                sys.exit()
                            else:
                                self.manager.set_scene(option["scene"])
                    for template in self.templates:
                        if template["rect"].collidepoint(mouse_pos):
                            self._start_with_template(template["template_id"])

    def draw(self, screen):
        self._refresh_fonts()
        self._draw_background(screen)
        
        # 标题与副标题
        title = self.title_font.render(self.manager.t("menu.title"), True, (255, 255, 255))
        title_x = self.width // 2 - title.get_width() // 2
        screen.blit(title, (title_x, 100 + self.top_offset))

        subtitle = self.subtitle_font.render(self.manager.t("menu.subtitle"), True, (170, 195, 235))
        screen.blit(subtitle, (self.width // 2 - subtitle.get_width() // 2, 170 + self.top_offset))
        
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
        screen.blit(hint, (self.width // 2 - hint.get_width() // 2, self.height - 40))

        template_title = self.hint_font.render(self.manager.t("menu.template_title"), True, (176, 200, 235))
        template_title_y = self.templates[0]["rect"].y - 28
        screen.blit(template_title, (self.width // 2 - template_title.get_width() // 2, template_title_y))

        for idx, template in enumerate(self.templates, start=5):
            rect = template["rect"]
            is_hovered = rect.collidepoint(mouse_pos)
            fill = (64, 103, 165) if is_hovered else (46, 77, 126)
            border = (162, 198, 246) if is_hovered else (114, 152, 210)
            pygame.draw.rect(screen, fill, rect, border_radius=10)
            pygame.draw.rect(screen, border, rect, 2, border_radius=10)
            label = self.template_font.render(f"{idx}. {self.manager.t(template['key'])}", True, (240, 246, 255))
            label_x = rect.centerx - label.get_width() // 2
            label_y = rect.centery - label.get_height() // 2
            screen.blit(label, (label_x, label_y))
