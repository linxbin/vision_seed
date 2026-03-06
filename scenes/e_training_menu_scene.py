import pygame

from config import SCREEN_HEIGHT, SCREEN_WIDTH
from core.base_scene import BaseScene


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
        start_y = 220
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
        screen.fill((8, 14, 26))
        title = self.title_font.render(self.manager.t("e_menu.title"), True, (238, 246, 255))
        subtitle = self.subtitle_font.render(self.manager.t("e_menu.subtitle"), True, (166, 188, 220))
        screen.blit(title, (self.width // 2 - title.get_width() // 2, 110))
        screen.blit(subtitle, (self.width // 2 - subtitle.get_width() // 2, 168))

        mouse_pos = pygame.mouse.get_pos()
        for item in self.items:
            hovered = item["rect"].collidepoint(mouse_pos)
            fill = (56, 86, 142) if hovered else (38, 58, 96)
            border = (172, 206, 255) if hovered else (108, 140, 194)
            pygame.draw.rect(screen, fill, item["rect"], border_radius=10)
            pygame.draw.rect(screen, border, item["rect"], 2, border_radius=10)
            text = self.option_font.render(f"{item['index']}. {item['label']}", True, (240, 246, 255))
            screen.blit(text, (item["rect"].x + 16, item["rect"].centery - text.get_height() // 2))

        hovered = self.back_rect.collidepoint(mouse_pos)
        fill = (68, 98, 152) if hovered else (50, 74, 118)
        border = (176, 210, 255) if hovered else (112, 145, 196)
        pygame.draw.rect(screen, fill, self.back_rect, border_radius=8)
        pygame.draw.rect(screen, border, self.back_rect, 2, border_radius=8)
        back_text = self.hint_font.render(self.manager.t("common.back"), True, (241, 247, 255))
        screen.blit(back_text, (self.back_rect.centerx - back_text.get_width() // 2, self.back_rect.centery - back_text.get_height() // 2))

        hint = self.hint_font.render(self.manager.t("e_menu.hint"), True, (148, 172, 206))
        screen.blit(hint, (self.width // 2 - hint.get_width() // 2, self.height - 34))
