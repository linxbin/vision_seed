import pygame
import sys

from config import SCREEN_HEIGHT, SCREEN_WIDTH
from core.base_scene import BaseScene


class MenuScene(BaseScene):
    def __init__(self, manager):
        super().__init__(manager)
        self._refresh_fonts()
        self.width = SCREEN_WIDTH
        self.height = SCREEN_HEIGHT
        self._items = []
        self.menu_options = []
        self.templates = []
        self._build_items()

    def _refresh_fonts(self):
        self.title_font = self.create_font(58)
        self.subtitle_font = self.create_font(24)
        self.option_font = self.create_font(28)
        self.hint_font = self.create_font(19)

    def _build_items(self):
        categories = self._safe_categories()
        card_w = min(680, self.width - 80)
        card_h = 52
        gap = 10
        start_y = 150
        start_x = self.width // 2 - card_w // 2

        self._items = []
        index = 1
        for category in categories:
            rect = pygame.Rect(start_x, start_y + (index - 1) * (card_h + gap), card_w, card_h)
            label = self._resolve_label(category)
            self._items.append(
                {
                    "index": index,
                    "rect": rect,
                    "kind": "category",
                    "category_id": category["id"],
                    "label": label,
                }
            )
            index += 1

        system_rect = pygame.Rect(start_x, start_y + (index - 1) * (card_h + gap), card_w, card_h)
        self._items.append(
            {"index": index, "rect": system_rect, "kind": "scene", "scene": "system_settings", "label": self.manager.t("menu.system_settings")}
        )
        index += 1

        exit_rect = pygame.Rect(start_x, start_y + (index - 1) * (card_h + gap), card_w, card_h)
        self._items.append({"index": index, "rect": exit_rect, "kind": "exit", "label": self.manager.t("menu.exit")})
        self._sync_legacy_ui_shape()

    def _safe_categories(self):
        categories = []
        registry = getattr(self.manager, "game_registry", None)
        if registry and hasattr(registry, "get_categories"):
            data = registry.get_categories()
            if isinstance(data, list):
                categories = data
        if categories:
            return categories
        return [
            {"id": "accommodation", "name": "Accommodation Training", "name_key": "category.accommodation"},
            {"id": "simultaneous", "name": "Simultaneous Vision Training", "name_key": "category.simultaneous"},
            {"id": "fusion", "name": "Fusion Training", "name_key": "category.fusion"},
            {"id": "suppression", "name": "Suppression Release Training", "name_key": "category.suppression"},
            {"id": "stereopsis", "name": "Stereopsis Training", "name_key": "category.stereopsis"},
            {"id": "amblyopia", "name": "Amblyopia Training", "name_key": "category.amblyopia"},
        ]

    def _resolve_label(self, item):
        name_key = item.get("name_key")
        if isinstance(name_key, str) and name_key:
            return self.manager.t(name_key)
        return item.get("name", "")

    def _sync_legacy_ui_shape(self):
        exit_item = next((item for item in self._items if item.get("kind") == "exit"), None)
        first_category = next((item for item in self._items if item.get("kind") == "category"), None)

        if first_category and exit_item:
            self.menu_options = [
                {"rect": first_category["rect"], "key": "menu.start_training", "scene": "training"},
                {
                    "rect": next((item for item in self._items if item.get("scene") == "system_settings"), first_category)["rect"],
                    "key": "menu.system_settings",
                    "scene": "system_settings",
                },
                {"rect": exit_item["rect"], "key": "menu.exit", "scene": "exit"},
            ]
        else:
            self.menu_options = []
        self.templates = []

    def on_enter(self):
        self._build_items()

    def on_resize(self, width, height):
        self.width = width
        self.height = height
        self._build_items()

    def _handle_item(self, item):
        kind = item["kind"]
        if kind == "category":
            self.manager.active_category = item["category_id"]
            self.manager.set_scene("category")
            return
        if kind == "scene":
            self.manager.set_scene(item["scene"])
            return
        pygame.quit()
        sys.exit()

    def handle_events(self, events):
        mouse_pos = pygame.mouse.get_pos()
        for event in events:
            if event.type == pygame.KEYDOWN:
                if pygame.K_1 <= event.key <= pygame.K_9:
                    idx = event.key - pygame.K_0
                    target = next((item for item in self._items if item["index"] == idx), None)
                    if target:
                        self._handle_item(target)
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                for item in self._items:
                    if item["rect"].collidepoint(mouse_pos):
                        self._handle_item(item)
                        break

    def draw(self, screen):
        self.refresh_fonts_if_needed()
        self._build_items()
        screen.fill((9, 14, 24))

        title = self.title_font.render(self.manager.t("menu.title"), True, (245, 248, 255))
        subtitle = self.subtitle_font.render(self.manager.t("menu.multigame_subtitle"), True, (162, 186, 226))
        screen.blit(title, (self.width // 2 - title.get_width() // 2, 46))
        screen.blit(subtitle, (self.width // 2 - subtitle.get_width() // 2, 108))

        mouse_pos = pygame.mouse.get_pos()
        for item in self._items:
            hovered = item["rect"].collidepoint(mouse_pos)
            fill = (56, 82, 130) if hovered else (34, 51, 82)
            border = (170, 202, 250) if hovered else (95, 124, 180)
            pygame.draw.rect(screen, fill, item["rect"], border_radius=8)
            pygame.draw.rect(screen, border, item["rect"], 2, border_radius=8)
            label = self.option_font.render(f"{item['index']}. {item['label']}", True, (238, 245, 255))
            screen.blit(label, (item["rect"].x + 14, item["rect"].centery - label.get_height() // 2))

        hint = self.hint_font.render(self.manager.t("menu.hint"), True, (146, 168, 204))
        screen.blit(hint, (self.width // 2 - hint.get_width() // 2, self.height - 34))
