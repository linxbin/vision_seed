import pygame
import sys

from config import SCREEN_HEIGHT, SCREEN_WIDTH
from core.base_scene import BaseScene
from core.training_recommendation import build_daily_plan, build_daily_suggestion
from core.ui_theme import PlatformTheme, draw_card, draw_chip, draw_platform_background


class MenuScene(BaseScene):
    def __init__(self, manager):
        super().__init__(manager)
        self._refresh_fonts()
        self.width = SCREEN_WIDTH
        self.height = SCREEN_HEIGHT
        self._items = []
        self.menu_options = []
        self.templates = []
        self.recommendations = []
        self.recommendation_hint = ""
        self.recommend_panel = pygame.Rect(0, 0, 1, 1)
        self.control_items = []
        self._recommendation_lines = 3
        self._compact_recommendation = False
        self._build_items()

    def _refresh_fonts(self):
        self.title_font = self.create_font(58)
        self.subtitle_font = self.create_font(24)
        self.option_font = self.create_font(28)
        self.hint_font = self.create_font(19)
        self.meta_font = self.create_font(17)
        self.badge_font = self.create_font(16)

    def _build_items(self):
        categories = self._safe_categories()
        margin = 32
        gutter = 18
        control_w = 180
        control_h = 50
        control_gap = 12
        control_x = self.width - margin - control_w
        exit_y = self.height - margin - control_h
        system_y = exit_y - control_gap - control_h
        self.control_items = [
            {"index": len(categories) + 1, "rect": pygame.Rect(control_x, system_y, control_w, control_h), "kind": "scene", "scene": "system_settings", "label": self.manager.t("menu.system_settings")},
            {"index": len(categories) + 2, "rect": pygame.Rect(control_x, exit_y, control_w, control_h), "kind": "exit", "label": self.manager.t("menu.exit")},
        ]

        bottom_reserved = 210
        start_y = 150
        available_h = max(240, self.height - start_y - bottom_reserved)
        card_gap = 10
        card_h = max(42, min(54, (available_h - card_gap * max(0, len(categories) - 1)) // max(1, len(categories))))
        card_w = min(620, self.width - 100)
        start_x = self.width // 2 - card_w // 2

        self._items = []
        for index, category in enumerate(categories, start=1):
            rect = pygame.Rect(start_x, start_y + (index - 1) * (card_h + card_gap), card_w, card_h)
            label = self._resolve_label(category)
            self._items.append({
                "index": index,
                "rect": rect,
                "kind": "category",
                "category_id": category["id"],
                "label": label,
            })

        rec_x = margin
        rec_y = self.height - 188
        rec_w = max(260, control_x - gutter - rec_x)
        rec_h = 132
        self.recommend_panel = pygame.Rect(rec_x, rec_y, rec_w, rec_h)
        self._compact_recommendation = self.width < 760 or self.height < 620
        self._recommendation_lines = 1 if self.width < 720 or self.height < 600 else (2 if self.width < 840 or self.height < 660 else 3)

        self.recommendations = build_daily_plan(self.manager, limit=3)
        self.recommendation_hint = build_daily_suggestion(self.manager, self.recommendations)
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
        exit_item = next((item for item in self.control_items if item.get("kind") == "exit"), None)
        system_item = next((item for item in self.control_items if item.get("scene") == "system_settings"), None)
        first_category = next((item for item in self._items if item.get("kind") == "category"), None)

        if first_category and exit_item and system_item:
            self.menu_options = [
                {"rect": first_category["rect"], "key": "menu.start_training", "scene": "training"},
                {"rect": system_item["rect"], "key": "menu.system_settings", "scene": "system_settings"},
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
                    target = next((item for item in self._items + self.control_items if item["index"] == idx), None)
                    if target:
                        self._handle_item(target)
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                for item in self._items + self.control_items:
                    if item["rect"].collidepoint(mouse_pos):
                        self._handle_item(item)
                        break

    def _draw_recommendations(self, screen):
        draw_card(screen, self.recommend_panel, alt=True, radius=18)
        title = self.option_font.render(self.manager.t("menu.recommend.title"), True, PlatformTheme.TEXT_PRIMARY)
        screen.blit(title, (self.recommend_panel.x + 16, self.recommend_panel.y + 12))

        if not self._compact_recommendation:
            badge_rect = pygame.Rect(self.recommend_panel.right - 112, self.recommend_panel.y + 14, 96, 28)
            draw_chip(screen, badge_rect, hovered=False)
            badge = self.badge_font.render("Today", True, PlatformTheme.ACCENT_DARK)
            screen.blit(badge, (badge_rect.centerx - badge.get_width() // 2, badge_rect.centery - badge.get_height() // 2))

        hint = self.meta_font.render(self.recommendation_hint, True, PlatformTheme.TEXT_MUTED)
        screen.blit(hint, (self.recommend_panel.x + 16, self.recommend_panel.y + 48))

        for idx, item in enumerate(self.recommendations[: self._recommendation_lines], start=1):
            reason = self.manager.t(item["reason_key"], accuracy=f"{item['accuracy']:.1f}")
            line = self.meta_font.render(f"{idx}. {item['game_name']}  ·  {reason}", True, PlatformTheme.TEXT_PRIMARY)
            screen.blit(line, (self.recommend_panel.x + 18, self.recommend_panel.y + 72 + (idx - 1) * 18))

    def draw(self, screen):
        self.refresh_fonts_if_needed()
        self._build_items()
        draw_platform_background(screen, self.width, self.height)

        title = self.title_font.render(self.manager.t("menu.title"), True, PlatformTheme.TEXT_PRIMARY)
        subtitle = self.subtitle_font.render(self.manager.t("menu.multigame_subtitle"), True, PlatformTheme.TEXT_MUTED)
        screen.blit(title, (self.width // 2 - title.get_width() // 2, 42))
        screen.blit(subtitle, (self.width // 2 - subtitle.get_width() // 2, 100))

        mouse_pos = pygame.mouse.get_pos()
        for item in self._items:
            hovered = item["rect"].collidepoint(mouse_pos)
            draw_card(screen, item["rect"], hovered=hovered)
            label = self.option_font.render(f"{item['index']}. {item['label']}", True, PlatformTheme.TEXT_PRIMARY)
            screen.blit(label, (item["rect"].x + 16, item["rect"].centery - label.get_height() // 2))

        for item in self.control_items:
            hovered = item["rect"].collidepoint(mouse_pos)
            draw_chip(screen, item["rect"], hovered=hovered)
            label = self.option_font.render(item["label"], True, PlatformTheme.ACCENT_DARK if not hovered else (255, 250, 244))
            screen.blit(label, (item["rect"].centerx - label.get_width() // 2, item["rect"].centery - label.get_height() // 2))

        self._draw_recommendations(screen)
        hint = self.hint_font.render(self.manager.t("menu.hint"), True, PlatformTheme.TEXT_MUTED)
        screen.blit(hint, (44, self.height - 34))
