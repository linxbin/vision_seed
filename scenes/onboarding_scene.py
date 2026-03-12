import pygame

from core.asset_loader import load_image_if_exists, project_path
from core.base_scene import BaseScene
from core.ui_theme import PlatformTheme, draw_card, draw_platform_background
from config import SCREEN_WIDTH, SCREEN_HEIGHT


class OnboardingScene(BaseScene):
    def __init__(self, manager):
        super().__init__(manager)
        self.width = SCREEN_WIDTH
        self.height = SCREEN_HEIGHT
        self._refresh_fonts()
        self._reflow_layout()

    def _refresh_fonts(self):
        self.title_font = self.create_font(44)
        self.subtitle_font = self.create_font(24)
        self.body_font = self.create_font(22)
        self.small_font = self.create_font(18)

    def _reflow_layout(self):
        panel_w = min(860, self.width - 80)
        panel_h = 460
        self.panel_rect = pygame.Rect(
            self.width // 2 - panel_w // 2,
            self.height // 2 - panel_h // 2,
            panel_w,
            panel_h,
        )
        self.start_button_rect = pygame.Rect(self.panel_rect.x + 80, self.panel_rect.bottom - 74, 180, 44)
        self.skip_button_rect = pygame.Rect(self.panel_rect.right - 260, self.panel_rect.bottom - 74, 180, 44)

    def on_resize(self, width, height):
        self.width = width
        self.height = height
        self._reflow_layout()

    def _complete_and_exit(self):
        self.manager.settings["onboarding_completed"] = True
        self.manager.save_user_preferences()
        self.manager.set_scene("menu")

    def handle_events(self, events):
        mouse_pos = pygame.mouse.get_pos()
        for event in events:
            if event.type == pygame.KEYDOWN:
                if event.key in (pygame.K_RETURN, pygame.K_SPACE):
                    self._complete_and_exit()
                elif event.key == pygame.K_ESCAPE:
                    self._complete_and_exit()
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if self.start_button_rect.collidepoint(mouse_pos) or self.skip_button_rect.collidepoint(mouse_pos):
                    self._complete_and_exit()

    def _draw_button(self, screen, rect, text, base_color):
        hovered = rect.collidepoint(pygame.mouse.get_pos())
        fill = tuple(min(c + 24, 255) for c in base_color) if hovered else base_color
        pygame.draw.rect(screen, fill, rect, border_radius=10)
        pygame.draw.rect(screen, (255, 245, 230), rect, 2, border_radius=10)
        icon_name = "check_light" if rect == self.start_button_rect else "cross_light"
        icon = load_image_if_exists(project_path("assets", "ui", f"{icon_name}.png"), (18, 18))
        label = self.body_font.render(text, True, (255, 255, 255))
        gap = 8 if icon is not None else 0
        content_width = label.get_width() + (icon.get_width() + gap if icon is not None else 0)
        start_x = rect.centerx - content_width // 2
        if icon is not None:
            screen.blit(icon, (start_x, rect.centery - icon.get_height() // 2))
            start_x += icon.get_width() + gap
        screen.blit(label, (start_x, rect.centery - label.get_height() // 2))

    def draw(self, screen):
        self.refresh_fonts_if_needed()
        draw_platform_background(screen, self.width, self.height)
        draw_card(screen, self.panel_rect, alt=True, radius=20)

        title = self.title_font.render(self.manager.t("onboarding.title"), True, PlatformTheme.TEXT_PRIMARY)
        screen.blit(title, (self.width // 2 - title.get_width() // 2, self.panel_rect.y + 24))

        subtitle = self.subtitle_font.render(self.manager.t("onboarding.subtitle"), True, PlatformTheme.TEXT_MUTED)
        screen.blit(subtitle, (self.width // 2 - subtitle.get_width() // 2, self.panel_rect.y + 82))

        tips = [
            self.manager.t("onboarding.tip1"),
            self.manager.t("onboarding.tip2"),
            self.manager.t("onboarding.tip3"),
            self.manager.t("onboarding.tip4"),
        ]
        tip_y = self.panel_rect.y + 150
        for idx, tip in enumerate(tips, start=1):
            tip_text = f"{idx}. {tip}"
            tip_surface = self.body_font.render(tip_text, True, PlatformTheme.TEXT_PRIMARY)
            screen.blit(tip_surface, (self.panel_rect.x + 52, tip_y))
            tip_y += 52

        est = self.small_font.render(self.manager.t("onboarding.estimate"), True, PlatformTheme.TEXT_MUTED)
        screen.blit(est, (self.panel_rect.x + 52, self.panel_rect.bottom - 112))

        self._draw_button(screen, self.start_button_rect, self.manager.t("onboarding.start"), (63, 154, 92))
        self._draw_button(screen, self.skip_button_rect, self.manager.t("onboarding.skip"), (88, 108, 152))
