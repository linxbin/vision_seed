import pygame

from config import MAX_SESSION_MINUTES, MIN_SESSION_MINUTES, SCREEN_HEIGHT, SCREEN_WIDTH
from core.base_scene import BaseScene
from core.asset_loader import load_image_if_exists, project_path
from core.ui_theme import PlatformTheme, draw_card, draw_chip_label, draw_platform_background


class SystemSettingsScene(BaseScene):
    def __init__(self, manager):
        super().__init__(manager)
        self._refresh_fonts()
        self.width = SCREEN_WIDTH
        self.height = SCREEN_HEIGHT
        self.sound_rect = pygame.Rect(0, 0, 1, 1)
        self.language_rect = pygame.Rect(0, 0, 1, 1)
        self.duration_rect = pygame.Rect(0, 0, 1, 1)
        self.back_rect = pygame.Rect(0, 0, 1, 1)
        self._reflow_layout()

    def _refresh_fonts(self):
        self.title_font = self.create_font(50)
        self.option_font = self.create_font(28)
        self.label_font = self.create_font(22)
        self.hint_font = self.create_font(20)

    def _reflow_layout(self):
        card_w = min(700, self.width - 80)
        card_h = 68
        x = self.width // 2 - card_w // 2
        y = 220
        gap = 18
        self.sound_rect = pygame.Rect(x, y, card_w, card_h)
        self.language_rect = pygame.Rect(x, y + card_h + gap, card_w, card_h)
        self.duration_rect = pygame.Rect(x, y + (card_h + gap) * 2, card_w, card_h)
        self.back_rect = pygame.Rect(self.width - 126, 24, 92, 40)

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

    def _cycle_session_duration(self):
        current = int(self.manager.settings.get("session_duration_minutes", 5))
        next_value = current + 1
        if next_value > MAX_SESSION_MINUTES:
            next_value = MIN_SESSION_MINUTES
        self.manager.settings["session_duration_minutes"] = next_value
        self.manager.save_user_preferences()

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
                elif event.key == pygame.K_3:
                    self._cycle_session_duration()
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if self.sound_rect.collidepoint(mouse_pos):
                    self._toggle_sound()
                elif self.language_rect.collidepoint(mouse_pos):
                    self._toggle_language()
                elif self.duration_rect.collidepoint(mouse_pos):
                    self._cycle_session_duration()
                elif self.back_rect.collidepoint(mouse_pos):
                    self._go_back()

    def _draw_item(self, screen, rect, text):
        mouse_pos = pygame.mouse.get_pos()
        hovered = rect.collidepoint(mouse_pos)
        draw_card(screen, rect, hovered=hovered)
        if rect == self.sound_rect:
            icon_name = "audio_on_dark" if self.manager.settings.get("sound_enabled", True) else "audio_off_dark"
        else:
            icon_name = "gear_dark"
        icon = load_image_if_exists(project_path("assets", "ui", f"{icon_name}.png"), (22, 22))
        label_x = rect.x + 18
        if icon is not None:
            screen.blit(icon, (label_x, rect.centery - icon.get_height() // 2))
            label_x += icon.get_width() + 12
        label = self.option_font.render(text, True, PlatformTheme.TEXT_PRIMARY)
        screen.blit(label, (label_x, rect.centery - label.get_height() // 2))

    def draw(self, screen):
        self.refresh_fonts_if_needed()
        draw_platform_background(screen, self.width, self.height)
        title = self.title_font.render(self.manager.t("system.title"), True, PlatformTheme.TEXT_PRIMARY)
        info = self.hint_font.render(self.manager.t("system.hint"), True, PlatformTheme.TEXT_MUTED)
        screen.blit(title, (self.width // 2 - title.get_width() // 2, 100))
        screen.blit(info, (self.width // 2 - info.get_width() // 2, 162))

        sound_on = self.manager.t("config.on") if self.manager.settings.get("sound_enabled", True) else self.manager.t("config.off")
        lang_text = self.manager.t("config.lang_en") if self.manager.settings.get("language") == "en-US" else self.manager.t("config.lang_zh")
        duration_text = self.manager.t("system.duration_value", n=int(self.manager.settings.get("session_duration_minutes", 5)))
        self._draw_item(screen, self.sound_rect, self.manager.t("system.sound", value=sound_on))
        self._draw_item(screen, self.language_rect, self.manager.t("system.language", value=lang_text))
        self._draw_item(screen, self.duration_rect, self.manager.t("system.duration", value=duration_text))

        mouse_pos = pygame.mouse.get_pos()
        hovered = self.back_rect.collidepoint(mouse_pos)
        draw_chip_label(screen, self.back_rect, self.label_font, self.manager.t("common.back"), hovered=hovered, icon_name="back_arrow")
