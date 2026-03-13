import pygame

from config import SCREEN_HEIGHT, SCREEN_WIDTH
from core.base_scene import BaseScene
from core.e_generator import EGenerator
from core.ui_theme import PlatformTheme, draw_card, draw_chip_label, draw_platform_background


E_TRAINING_GAME_ID = "accommodation.e_orientation"


class ETrainingMenuScene(BaseScene):
    def __init__(self, manager):
        super().__init__(manager)
        self._refresh_fonts()
        self.width = SCREEN_WIDTH
        self.height = SCREEN_HEIGHT
        self.items = []
        self.back_rect = pygame.Rect(0, 0, 1, 1)
        self._build_items()

    def _refresh_fonts(self):
        self.title_font = self.create_font(52)
        self.subtitle_font = self.create_font(24)
        self.option_font = self.create_font(30)
        self.hint_font = self.create_font(20)

    def _build_items(self):
        card_w = min(620, self.width - 100)
        card_h = 58
        gap = 14
        total_h = card_h * 4 + gap * 3
        available_top = 190
        available_bottom = self.height - 90
        available_h = max(total_h, available_bottom - available_top)
        start_y = available_top + max(0, (available_h - total_h) // 2)
        x = self.width // 2 - card_w // 2
        labels = [
            (self.manager.t("e_menu.start"), "training"),
            (self.manager.t("e_menu.config"), "config"),
            (self.manager.t("e_menu.history"), "history"),
            (self.manager.t("common.back"), "category"),
        ]
        self.items = []
        for index, (label, scene_name) in enumerate(labels, start=1):
            rect = pygame.Rect(x, start_y + (index - 1) * (card_h + gap), card_w, card_h)
            self.items.append({"index": index, "label": label, "scene": scene_name, "rect": rect})
        self.back_rect = pygame.Rect(self.width - 98, 20, 78, 34)

    def reset(self):
        # Game host expects a reset method when mounting game entry scene.
        return

    def on_resize(self, width, height):
        self.width = width
        self.height = height
        self._build_items()

    def on_enter(self):
        self._build_items()

    def _ensure_scope(self):
        if getattr(self.manager, "active_game_id", None) != E_TRAINING_GAME_ID:
            self.manager.set_scene("menu")
            return False
        return True

    def _goto(self, scene_name):
        if scene_name == "category":
            self.manager.set_scene("category")
        else:
            self.manager.set_scene(scene_name)

    def handle_events(self, events):
        if not self._ensure_scope():
            return
        mouse_pos = pygame.mouse.get_pos()
        for event in events:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.manager.set_scene("category")
                    continue
                if pygame.K_1 <= event.key <= pygame.K_9:
                    idx = event.key - pygame.K_0
                    item = next((it for it in self.items if it["index"] == idx), None)
                    if item:
                        self._goto(item["scene"])
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if self.back_rect.collidepoint(mouse_pos):
                    self.manager.set_scene("category")
                    continue
                for item in self.items:
                    if item["rect"].collidepoint(mouse_pos):
                        self._goto(item["scene"])
                        break

    def draw(self, screen):
        self.refresh_fonts_if_needed()
        draw_platform_background(screen, self.width, self.height)
        title = self.title_font.render(self.manager.t("e_menu.title"), True, PlatformTheme.TEXT_PRIMARY)
        subtitle = self.subtitle_font.render(self.manager.t("e_menu.subtitle"), True, PlatformTheme.TEXT_MUTED)
        screen.blit(title, (self.width // 2 - title.get_width() // 2, 110))
        screen.blit(subtitle, (self.width // 2 - subtitle.get_width() // 2, 168))

        mouse_pos = pygame.mouse.get_pos()
        for index, item in enumerate(self.items, start=1):
            hovered = item["rect"].collidepoint(mouse_pos)
            draw_card(screen, item["rect"], hovered=hovered, alt=index % 2 == 0)
            text = self.option_font.render(f"{item['index']}. {item['label']}", True, PlatformTheme.TEXT_PRIMARY)
            screen.blit(text, (item["rect"].x + 16, item["rect"].centery - text.get_height() // 2))

        hovered = self.back_rect.collidepoint(mouse_pos)
        draw_chip_label(screen, self.back_rect, self.hint_font, self.manager.t("common.back"), hovered=hovered, icon_name="back_arrow")

        hint = self.hint_font.render(self.manager.t("e_menu.hint"), True, PlatformTheme.TEXT_MUTED)
        screen.blit(hint, (self.width // 2 - hint.get_width() // 2, self.height - 34))
