import pygame
import sys

from config import SCREEN_HEIGHT, SCREEN_WIDTH
from core.asset_loader import load_image_if_exists, project_path
from core.base_scene import BaseScene
from core.training_recommendation import build_daily_plan, build_daily_suggestion, build_recent_completions
from core.ui_theme import PlatformTheme, draw_card, draw_chip_label, draw_platform_background


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
        self.recent_completions = []
        self.recommend_panel = pygame.Rect(0, 0, 1, 1)
        self._recent_row_y = 0
        self.control_items = []
        self._recommendation_lines = 3
        self._compact_recommendation = False
        self.focused_index = 0
        self._build_items()

    def _refresh_fonts(self):
        self.title_font = self.create_font(58)
        self.subtitle_font = self.create_font(24)
        self.option_font = self.create_font(28)
        self.hint_font = self.create_font(19)
        self.meta_font = self.create_font(17)
        self.badge_font = self.create_font(16)

    def _build_items(self):
        previous_focus = self.focused_index
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
            {"index": len(categories) + 1, "rect": pygame.Rect(control_x, system_y, control_w, control_h), "kind": "scene", "scene": "system_settings", "label": self.manager.t("menu.system_settings"), "icon": "gear"},
            {"index": len(categories) + 2, "rect": pygame.Rect(control_x, exit_y, control_w, control_h), "kind": "exit", "label": self.manager.t("menu.exit"), "icon": "power"},
        ]

        bottom_reserved = 236
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
        rec_y = self.height - 224
        rec_w = max(260, control_x - gutter - rec_x)
        rec_h = 170
        self.recommend_panel = pygame.Rect(rec_x, rec_y, rec_w, rec_h)
        self._compact_recommendation = self.width < 760 or self.height < 620
        self._recommendation_lines = 1 if self.width < 720 or self.height < 600 else (2 if self.width < 840 or self.height < 660 else 3)

        self.recommendations = build_daily_plan(self.manager, limit=3)
        self.recommendation_hint = build_daily_suggestion(self.manager, self.recommendations)
        self.recent_completions = build_recent_completions(self.manager, limit=2)
        self._recent_row_y = self.recommend_panel.bottom - 38
        self._sync_legacy_ui_shape()
        if self._all_items():
            self.focused_index = max(0, min(previous_focus, len(self._all_items()) - 1))

    def _all_items(self):
        return self._items + self.control_items

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
            {"id": "accommodation", "name": self.manager.t("category.accommodation"), "name_key": "category.accommodation"},
            {"id": "simultaneous", "name": self.manager.t("category.simultaneous"), "name_key": "category.simultaneous"},
            {"id": "fusion", "name": self.manager.t("category.fusion"), "name_key": "category.fusion"},
            {"id": "suppression", "name": self.manager.t("category.suppression"), "name_key": "category.suppression"},
            {"id": "stereopsis", "name": self.manager.t("category.stereopsis"), "name_key": "category.stereopsis"},
            {"id": "amblyopia", "name": self.manager.t("category.amblyopia"), "name_key": "category.amblyopia"},
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
                all_items = self._all_items()
                if event.key in (pygame.K_UP, pygame.K_LEFT) and all_items:
                    self.focused_index = (self.focused_index - 1) % len(all_items)
                    continue
                if event.key in (pygame.K_DOWN, pygame.K_RIGHT) and all_items:
                    self.focused_index = (self.focused_index + 1) % len(all_items)
                    continue
                if event.key in (pygame.K_RETURN, pygame.K_SPACE) and all_items:
                    self._handle_item(all_items[self.focused_index])
                    continue
                if pygame.K_1 <= event.key <= pygame.K_9:
                    idx = event.key - pygame.K_0
                    target = next((item for item in all_items if item["index"] == idx), None)
                    if target:
                        self._handle_item(target)
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                for idx, item in enumerate(self._all_items()):
                    if item["rect"].collidepoint(mouse_pos):
                        self.focused_index = idx
                        self._handle_item(item)
                        break

    def _draw_recommendations(self, screen):
        draw_card(screen, self.recommend_panel, alt=True, radius=18)
        target_icon = load_image_if_exists(project_path("assets", "ui", "target_dark.png"), (18, 18))
        title = self.option_font.render(self.manager.t("menu.recommend.title"), True, PlatformTheme.TEXT_PRIMARY)
        title_x = self.recommend_panel.x + 16
        if target_icon is not None:
            screen.blit(target_icon, (title_x, self.recommend_panel.y + 16))
            title_x += target_icon.get_width() + 8
        screen.blit(title, (title_x, self.recommend_panel.y + 12))

        if not self._compact_recommendation:
            badge_rect = pygame.Rect(self.recommend_panel.right - 112, self.recommend_panel.y + 14, 96, 28)

        text_left = self.recommend_panel.x + 16
        text_width = self.recommend_panel.width - 32
        hint_lines, hint_height = self.draw_text_block(
            screen,
            self.meta_font,
            self.recommendation_hint,
            PlatformTheme.TEXT_MUTED,
            (text_left, self.recommend_panel.y + 48),
            text_width,
            line_gap=2,
            max_lines=2,
            ellipsis=True,
        )
        recommendation_start_y = self.recommend_panel.y + 54 + hint_height

        for idx, item in enumerate(self.recommendations[: self._recommendation_lines], start=1):
            reason = self.manager.t(item["reason_key"], accuracy=f"{item['accuracy']:.1f}")
            line_text = self.fit_text_to_width(
                self.meta_font,
                f"{idx}. {item['game_name']}  ·  {reason}",
                self.recommend_panel.width - 44,
            )
            line = self.meta_font.render(line_text, True, PlatformTheme.TEXT_PRIMARY)
            line_y = recommendation_start_y + (idx - 1) * 18
            bullet_icon = load_image_if_exists(project_path("assets", "ui", "star_dark.png"), (12, 12))
            line_x = self.recommend_panel.x + 18
            if bullet_icon is not None:
                screen.blit(bullet_icon, (line_x, line_y + 3))
                line_x += bullet_icon.get_width() + 6
            screen.blit(line, (line_x, line_y))

        recent_title = self.meta_font.render(self.manager.t("menu.recent.title"), True, PlatformTheme.TEXT_PRIMARY)
        recent_y = max(self._recent_row_y + 4, recommendation_start_y + self._recommendation_lines * 18 + 8)
        divider_y = recent_y - 12
        pygame.draw.line(
            screen,
            PlatformTheme.BORDER,
            (self.recommend_panel.x + 14, divider_y),
            (self.recommend_panel.right - 14, divider_y),
            1,
        )
        screen.blit(recent_title, (self.recommend_panel.x + 16, recent_y))
        if self.recent_completions:
            parts = []
            for item in self.recent_completions[:2]:
                parts.append(
                    self.manager.t(
                        "menu.recent.item",
                        game=item["game_name"],
                        accuracy=f"{item['accuracy']:.1f}",
                    )
                )
            recent_text = self.meta_font.render(
                self.fit_text_to_width(self.meta_font, "  |  ".join(parts), self.recommend_panel.width - 134),
                True,
                PlatformTheme.TEXT_MUTED,
            )
            screen.blit(recent_text, (self.recommend_panel.x + 118, recent_y))
        else:
            empty = self.meta_font.render(
                self.fit_text_to_width(self.meta_font, self.manager.t("menu.recent.none"), self.recommend_panel.width - 134),
                True,
                PlatformTheme.TEXT_MUTED,
            )
            screen.blit(empty, (self.recommend_panel.x + 118, recent_y))

    def draw(self, screen):
        self.refresh_fonts_if_needed()
        draw_platform_background(screen, self.width, self.height)

        title = self.title_font.render(self.manager.t("menu.title"), True, PlatformTheme.TEXT_PRIMARY)
        subtitle = self.subtitle_font.render(self.manager.t("menu.multigame_subtitle"), True, PlatformTheme.TEXT_MUTED)
        screen.blit(title, (self.width // 2 - title.get_width() // 2, 42))
        screen.blit(subtitle, (self.width // 2 - subtitle.get_width() // 2, 100))

        mouse_pos = pygame.mouse.get_pos()
        all_items = self._all_items()
        for idx, item in enumerate(self._items):
            hovered = item["rect"].collidepoint(mouse_pos) or idx == self.focused_index
            draw_card(screen, item["rect"], hovered=hovered)
            label = self.option_font.render(f"{item['index']}. {item['label']}", True, PlatformTheme.TEXT_PRIMARY)
            screen.blit(label, (item["rect"].x + 16, item["rect"].centery - label.get_height() // 2))

        for offset, item in enumerate(self.control_items, start=len(self._items)):
            hovered = item["rect"].collidepoint(mouse_pos) or offset == self.focused_index
            draw_chip_label(
                screen,
                item["rect"],
                self.option_font,
                item["label"],
                hovered=hovered,
                icon_name=item.get("icon"),
            )

        self._draw_recommendations(screen)
        hint = self.hint_font.render(self.manager.t("menu.hint"), True, PlatformTheme.TEXT_MUTED)
        screen.blit(hint, (44, self.height - 34))
