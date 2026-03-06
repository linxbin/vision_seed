import pygame

from config import SCREEN_HEIGHT, SCREEN_WIDTH
from core.base_scene import BaseScene


class SystemSettingsScene(BaseScene):
    def __init__(self, manager):
        super().__init__(manager)
        self._refresh_fonts()
        self.width = SCREEN_WIDTH
        self.height = SCREEN_HEIGHT
        self.sound_rect = pygame.Rect(0, 0, 1, 1)
        self.language_rect = pygame.Rect(0, 0, 1, 1)
        self.back_rect = pygame.Rect(0, 0, 1, 1)
        self._reflow_layout()

    def _refresh_fonts(self):
        self.title_font = self.create_font(50)
        self.option_font = self.create_font(28)
        self.label_font = self.create_font(22)
        self.hint_font = self.create_font(20)

    def _reflow_layout(self):
        card_w = min(700, self.width - 80)
        card_h = 64
        x = self.width // 2 - card_w // 2
        y = 220
        gap = 18
        self.sound_rect = pygame.Rect(x, y, card_w, card_h)
        self.language_rect = pygame.Rect(x, y + card_h + gap, card_w, card_h)
        self.back_rect = pygame.Rect(self.width - 98, 20, 78, 34)

    def on_resize(self, width, height):
        self.width = width
        self.height = height
        self._reflow_layout()

    def _toggle_sound(self):
        self.manager.settings["sound_enabled"] = not bool(self.manager.settings.get("sound_enabled", True))
        self.manager.apply_sound_preference()
        self.manager.save_user_preferences()

    def _toggle_language(self):
        self.manager.settings["language"] = "zh-CN" if self.manager.settings.get("language") == "en-US" else "en-US"
        self.manager.apply_language_preference()
        self.manager.save_user_preferences()

    def _go_back(self):
        self.manager.set_scene("menu")

    def handle_events(self, events):
        mouse_pos = pygame.mouse.get_pos()
        for event in events:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self._go_back()
                elif event.key == pygame.K_1:
                    self._toggle_sound()
                elif event.key == pygame.K_2:
                    self._toggle_language()
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if self.sound_rect.collidepoint(mouse_pos):
                    self._toggle_sound()
                elif self.language_rect.collidepoint(mouse_pos):
                    self._toggle_language()
                elif self.back_rect.collidepoint(mouse_pos):
                    self._go_back()

    def _draw_item(self, screen, rect, text):
        mouse_pos = pygame.mouse.get_pos()
        hovered = rect.collidepoint(mouse_pos)
        fill = (60, 88, 138) if hovered else (42, 62, 98)
        border = (172, 206, 255) if hovered else (108, 140, 194)
        pygame.draw.rect(screen, fill, rect, border_radius=10)
        pygame.draw.rect(screen, border, rect, 2, border_radius=10)
        label = self.option_font.render(text, True, (240, 246, 255))
        screen.blit(label, (rect.x + 16, rect.centery - label.get_height() // 2))

    def draw(self, screen):
        self.refresh_fonts_if_needed()
        screen.fill((9, 14, 24))
        title = self.title_font.render(self.manager.t("system.title"), True, (245, 248, 255))
        info = self.hint_font.render(self.manager.t("system.hint"), True, (156, 182, 222))
        screen.blit(title, (self.width // 2 - title.get_width() // 2, 100))
        screen.blit(info, (self.width // 2 - info.get_width() // 2, 162))

        sound_on = self.manager.t("config.on") if self.manager.settings.get("sound_enabled", True) else self.manager.t("config.off")
        lang_text = self.manager.t("config.lang_en") if self.manager.settings.get("language") == "en-US" else self.manager.t("config.lang_zh")
        self._draw_item(screen, self.sound_rect, self.manager.t("system.sound", value=sound_on))
        self._draw_item(screen, self.language_rect, self.manager.t("system.language", value=lang_text))

        mouse_pos = pygame.mouse.get_pos()
        hovered = self.back_rect.collidepoint(mouse_pos)
        fill = (68, 98, 152) if hovered else (50, 74, 118)
        border = (176, 210, 255) if hovered else (112, 145, 196)
        pygame.draw.rect(screen, fill, self.back_rect, border_radius=8)
        pygame.draw.rect(screen, border, self.back_rect, 2, border_radius=8)
        back_text = self.label_font.render(self.manager.t("common.back"), True, (241, 247, 255))
        screen.blit(back_text, (self.back_rect.centerx - back_text.get_width() // 2, self.back_rect.centery - back_text.get_height() // 2))
