import pygame

from core.base_scene import BaseScene
from config import SCREEN_HEIGHT, SCREEN_WIDTH


class CategoryScene(BaseScene):
    def __init__(self, manager):
        super().__init__(manager)
        self._refresh_fonts()
        self.width = SCREEN_WIDTH
        self.height = SCREEN_HEIGHT
        self._items = []
        self._title = ""
        self.back_rect = pygame.Rect(0, 0, 1, 1)
        self._build_items()

    def _refresh_fonts(self):
        self.title_font = self.create_font(48)
        self.item_font = self.create_font(30)
        self.hint_font = self.create_font(20)

    def _build_items(self):
        category_id = self.manager.active_category
        categories = self.manager.game_registry.get_categories()
        category_item = next((item for item in categories if item["id"] == category_id), None)
        category_name = self._resolve_label(category_item) if category_item else self.manager.t("category.unknown")
        self._title = category_name

        games = self.manager.game_registry.get_games_by_category(category_id)
        self._items = []
        card_w = min(640, self.width - 80)
        card_h = 56
        gap = 14
        start_y = 170
        x = self.width // 2 - card_w // 2

        for index, game in enumerate(games, start=1):
            rect = pygame.Rect(x, start_y + (index - 1) * (card_h + gap), card_w, card_h)
            game_name = self.manager.t(game.name_key) if getattr(game, "name_key", "") else game.name
            self._items.append({"rect": rect, "index": index, "game_id": game.game_id, "name": game_name})
        self.back_rect = pygame.Rect(self.width - 98, 20, 78, 34)

    def _resolve_label(self, item):
        if not item:
            return ""
        name_key = item.get("name_key")
        if isinstance(name_key, str) and name_key:
            return self.manager.t(name_key)
        return item.get("name", "")

    def on_enter(self):
        self._build_items()

    def on_resize(self, width, height):
        self.width = width
        self.height = height
        self._build_items()

    def _enter_game(self, game_id: str):
        self.manager.active_game_id = game_id
        self.manager.set_scene("game_host")

    def handle_events(self, events):
        mouse_pos = pygame.mouse.get_pos()
        for event in events:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.manager.set_scene("menu")
                    continue

                if pygame.K_1 <= event.key <= pygame.K_9:
                    idx = event.key - pygame.K_0
                    target = next((item for item in self._items if item["index"] == idx), None)
                    if target:
                        self._enter_game(target["game_id"])
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if self.back_rect.collidepoint(mouse_pos):
                    self.manager.set_scene("menu")
                    continue
                for item in self._items:
                    if item["rect"].collidepoint(mouse_pos):
                        self._enter_game(item["game_id"])
                        break

    def draw(self, screen):
        self.refresh_fonts_if_needed()
        screen.fill((10, 14, 22))

        title = self.title_font.render(self._title, True, (236, 244, 255))
        screen.blit(title, (self.width // 2 - title.get_width() // 2, 72))

        if not self._items:
            empty_text = self.item_font.render(self.manager.t("category.empty"), True, (168, 184, 212))
            screen.blit(empty_text, (self.width // 2 - empty_text.get_width() // 2, self.height // 2 - 20))
        else:
            mouse_pos = pygame.mouse.get_pos()
            for item in self._items:
                hovered = item["rect"].collidepoint(mouse_pos)
                fill = (54, 78, 122) if hovered else (35, 50, 80)
                border = (164, 196, 245) if hovered else (98, 124, 174)
                pygame.draw.rect(screen, fill, item["rect"], border_radius=8)
                pygame.draw.rect(screen, border, item["rect"], 2, border_radius=8)
                label = self.item_font.render(f"{item['index']}. {item['name']}", True, (236, 244, 255))
                label_x = item["rect"].x + 16
                label_y = item["rect"].centery - label.get_height() // 2
                screen.blit(label, (label_x, label_y))

        mouse_pos = pygame.mouse.get_pos()
        hovered = self.back_rect.collidepoint(mouse_pos)
        fill = (68, 98, 152) if hovered else (50, 74, 118)
        border = (176, 210, 255) if hovered else (112, 145, 196)
        pygame.draw.rect(screen, fill, self.back_rect, border_radius=8)
        pygame.draw.rect(screen, border, self.back_rect, 2, border_radius=8)
        back_text = self.hint_font.render(self.manager.t("common.back"), True, (241, 247, 255))
        screen.blit(back_text, (self.back_rect.centerx - back_text.get_width() // 2, self.back_rect.centery - back_text.get_height() // 2))

        hint = self.hint_font.render(self.manager.t("category.hint"), True, (148, 166, 198))
        screen.blit(hint, (self.width // 2 - hint.get_width() // 2, self.height - 36))
