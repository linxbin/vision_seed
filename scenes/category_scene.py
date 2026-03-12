import pygame

from core.base_scene import BaseScene
from core.game_metrics import summarize_session
from core.ui_theme import PlatformTheme, draw_card, draw_chip_label, draw_platform_background
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
        self.meta_font = self.create_font(16)

    def _build_items(self):
        category_id = self.manager.active_category
        categories = self.manager.game_registry.get_categories()
        category_item = next((item for item in categories if item["id"] == category_id), None)
        category_name = self._resolve_label(category_item) if category_item else self.manager.t("category.unknown")
        self._title = category_name

        games = self.manager.game_registry.get_games_by_category(category_id)
        self._items = []
        card_w = min(660, self.width - 80)
        card_h = 84
        gap = 14
        start_y = 170
        x = self.width // 2 - card_w // 2

        for index, game in enumerate(games, start=1):
            rect = pygame.Rect(x, start_y + (index - 1) * (card_h + gap), card_w, card_h)
            game_name = self.manager.t(game.name_key) if getattr(game, "name_key", "") else game.name
            latest = self.manager.data_manager.get_latest_session(game.game_id)
            summary1, summary2 = summarize_session(self.manager, latest)
            self._items.append({"rect": rect, "index": index, "game_id": game.game_id, "name": game_name, "summary1": summary1, "summary2": summary2})
        self.back_rect = pygame.Rect(self.width - 126, 24, 92, 40)

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
        draw_platform_background(screen, self.width, self.height)

        title = self.title_font.render(self._title, True, PlatformTheme.TEXT_PRIMARY)
        screen.blit(title, (self.width // 2 - title.get_width() // 2, 72))

        if not self._items:
            empty_text = self.item_font.render(self.manager.t("category.empty"), True, PlatformTheme.TEXT_MUTED)
            screen.blit(empty_text, (self.width // 2 - empty_text.get_width() // 2, self.height // 2 - 20))
        else:
            mouse_pos = pygame.mouse.get_pos()
            for index, item in enumerate(self._items, start=1):
                hovered = item["rect"].collidepoint(mouse_pos)
                draw_card(screen, item["rect"], hovered=hovered, alt=index % 2 == 0)
                label = self.item_font.render(f"{item['index']}. {item['name']}", True, PlatformTheme.TEXT_PRIMARY)
                label_x = item["rect"].x + 16
                label_y = item["rect"].y + 12
                screen.blit(label, (label_x, label_y))
                if item.get("summary1"):
                    summary1 = self.meta_font.render(item["summary1"], True, PlatformTheme.TEXT_MUTED)
                    screen.blit(summary1, (label_x, item["rect"].y + 44))
                if item.get("summary2"):
                    summary2 = self.meta_font.render(item["summary2"], True, (124, 145, 170))
                    screen.blit(summary2, (label_x, item["rect"].y + 62))

        mouse_pos = pygame.mouse.get_pos()
        hovered = self.back_rect.collidepoint(mouse_pos)
        draw_chip_label(screen, self.back_rect, self.hint_font, self.manager.t("common.back"), hovered=hovered, icon_name="back_arrow")

        hint = self.hint_font.render(self.manager.t("category.hint"), True, PlatformTheme.TEXT_MUTED)
        screen.blit(hint, (self.width // 2 - hint.get_width() // 2, self.height - 36))
