import pygame
from core.base_scene import BaseScene
from core.e_generator import EGenerator
from core.ui_theme import PlatformTheme, draw_card, draw_platform_background
from config import E_SIZE_LEVELS, SCREEN_WIDTH, MIN_QUESTIONS, MAX_QUESTIONS


class ConfigScene(BaseScene):
    E_TRAINING_GAME_ID = "accommodation.e_orientation"
    BASE_WIDTH = SCREEN_WIDTH
    BASE_HEIGHT = 700

    PANEL_RADIUS = 12
    CONTROL_RADIUS = 8
    BUTTON_RADIUS = 9

    MARGIN_X = 40
    TOP_TITLE_Y = 28
    TOP_INFO_Y = 80

    LEVEL_PANEL = (40, 105, 380, 235)
    PREVIEW_PANEL = (440, 105, 420, 235)
    # 题量与偏好区保持同尺寸、同Y轴并行排版
    QUESTION_PANEL = (40, 345, 380, 190)
    PREF_PANEL = (440, 345, 420, 190)
    PREF_INSET_X = 25
    PREF_TOGGLE_W = 180
    PREF_TOGGLE_H = 36
    PREF_ROW1_Y = 60
    PREF_ROW2_Y = 126
    PREF_DESC_Y = 170
    PREF_COL2_X = 215

    ACTION_BUTTON_Y = 560
    ACTION_BUTTON_W = 130
    ACTION_BUTTON_H = 42
    ACTION_BUTTON_GAP = 12
    FEEDBACK_DURATION_FRAMES = 180

    COLOR_BG = PlatformTheme.BG_BOTTOM
    COLOR_PANEL_FILL = PlatformTheme.CARD
    COLOR_PANEL_FILL_HOVER = PlatformTheme.CARD_HOVER
    COLOR_PANEL_BORDER = PlatformTheme.BORDER
    COLOR_PANEL_BORDER_HOVER = PlatformTheme.BORDER_HOVER

    def __init__(self, manager):
        super().__init__(manager)
        self._refresh_fonts()
        self.e_generator = EGenerator()

        self.width = SCREEN_WIDTH
        self.height = 700
        self.layout_offset_x = 0
        self.layout_offset_y = 0

        self.draft_settings = {}
        self.original_settings = {}
        self._sync_state_from_manager()

        self.input_active = False
        self.input_text = str(self.draft_settings["total_questions"])
        self.input_error = ""

        self.hovered_level = None
        self.level_flash_frames = 0
        self.level_flash_level = self.draft_settings["start_level"]

        self.level_cards = []
        self.feedback_message = ""
        self.feedback_variant = "info"
        self.feedback_frames = 0
        self._reflow_layout()

    def _sync_state_from_manager(self):
        source = {
            "start_level": self.manager.settings["start_level"],
            "total_questions": self.manager.settings["total_questions"],
            "adaptive_enabled": self.manager.settings.get("adaptive_enabled", True),
        }
        self.original_settings = dict(source)
        self.draft_settings = dict(source)

    def _refresh_fonts(self):
        self.font = self.create_font(24)
        # 与训练历史页保持一致规格，不额外加粗
        self.title_font = self.create_font(48)
        self.subtitle_font = self.create_font(26)
        self.small_font = self.create_font(18)
        self.tiny_font = self.create_font(15)

    def _fit_text(self, text, font, max_width):
        if font.size(text)[0] <= max_width:
            return text
        ellipsis = "..."
        trimmed = text
        while trimmed and font.size(trimmed + ellipsis)[0] > max_width:
            trimmed = trimmed[:-1]
        return (trimmed + ellipsis) if trimmed else ellipsis

    def on_enter(self):
        if not self._ensure_scope():
            return
        self._sync_state_from_manager()
        self.input_text = str(self.draft_settings["total_questions"])
        self.input_error = ""
        self.input_active = False
        self.feedback_message = ""
        self.feedback_variant = "info"
        self.feedback_frames = 0

    def _ensure_scope(self):
        game_id = getattr(self.manager, "active_game_id", None)
        if isinstance(game_id, str) and game_id and game_id != self.E_TRAINING_GAME_ID:
            self.manager.set_scene("menu")
            return False
        return True

    def _return_scene_name(self):
        if getattr(self.manager, "active_game_id", None) == self.E_TRAINING_GAME_ID:
            return "game_host"
        return "menu"

    def update(self):
        if self.level_flash_frames > 0:
            self.level_flash_frames -= 1
        if self.feedback_frames > 0:
            self.feedback_frames -= 1

    def _set_feedback(self, key, variant="info", **kwargs):
        self.feedback_message = self.manager.t(key, **kwargs)
        self.feedback_variant = variant
        self.feedback_frames = self.FEEDBACK_DURATION_FRAMES

    def _create_ui_elements(self):
        offset_x = self.layout_offset_x
        offset_y = self.layout_offset_y

        self.title_y = offset_y + self.TOP_TITLE_Y
        self.info_y = offset_y + self.TOP_INFO_Y

        self.level_panel_rect = pygame.Rect(offset_x + self.LEVEL_PANEL[0], offset_y + self.LEVEL_PANEL[1], self.LEVEL_PANEL[2], self.LEVEL_PANEL[3])
        self.preview_panel_rect = pygame.Rect(offset_x + self.PREVIEW_PANEL[0], offset_y + self.PREVIEW_PANEL[1], self.PREVIEW_PANEL[2], self.PREVIEW_PANEL[3])
        self.question_panel_rect = pygame.Rect(offset_x + self.QUESTION_PANEL[0], offset_y + self.QUESTION_PANEL[1], self.QUESTION_PANEL[2], self.QUESTION_PANEL[3])
        self.pref_panel_rect = pygame.Rect(offset_x + self.PREF_PANEL[0], offset_y + self.PREF_PANEL[1], self.PREF_PANEL[2], self.PREF_PANEL[3])

        level_count = len(E_SIZE_LEVELS)
        self.level_cards = []
        self.level_groups = []

        # 10级模式：按挑战/标准/入门分组显示，避免纯平铺密集感
        if level_count == 10:
            group_defs = [
                ("config.group_challenge", [1, 2, 3]),
                ("config.group_standard", [4, 5, 6, 7]),
                ("config.group_entry", [8, 9, 10]),
            ]
            inner_x = self.level_panel_rect.x + 14
            inner_y = self.level_panel_rect.y + 56
            inner_w = self.level_panel_rect.width - 28
            group_gap = 10
            group_w = (inner_w - group_gap * 2) // 3
            group_h = 166

            for idx, (title_key, levels) in enumerate(group_defs):
                gx = inner_x + idx * (group_w + group_gap)
                group_rect = pygame.Rect(gx, inner_y, group_w, group_h)
                self.level_groups.append(
                    {
                        "title_key": title_key,
                        "rect": group_rect,
                        "levels": levels,
                    }
                )

                card_x = group_rect.x + 7
                card_w = group_rect.width - 14
                card_h = 28
                card_gap = 6
                card_start_y = group_rect.y + 26
                for j, level in enumerate(levels):
                    card_y = card_start_y + j * (card_h + card_gap)
                    self.level_cards.append((pygame.Rect(card_x, card_y, card_w, card_h), level))
        else:
            compact = level_count > 8
            columns = 5 if compact else 4
            card_w = 62 if compact else 78
            card_h = 42 if compact else 52
            card_gap = 8 if compact else 12
            start_x = self.level_panel_rect.x + 18
            start_y = self.level_panel_rect.y + 58
            for i in range(level_count):
                row = i // columns
                col = i % columns
                x = start_x + col * (card_w + card_gap)
                y = start_y + row * (card_h + card_gap)
                self.level_cards.append((pygame.Rect(x, y, card_w, card_h), i + 1))

        self.input_rect = pygame.Rect(self.question_panel_rect.x + 30, self.question_panel_rect.y + 76, 140, 40)
        self.minus_button_rect = pygame.Rect(self.input_rect.right + 14, self.input_rect.y, 40, 40)
        self.plus_button_rect = pygame.Rect(self.minus_button_rect.right + 10, self.input_rect.y, 40, 40)

        # 偏好区仅保留自适应开关
        self.adaptive_toggle_rect = pygame.Rect(
            self.pref_panel_rect.x + self.PREF_INSET_X,
            self.pref_panel_rect.y + self.PREF_ROW1_Y + 10,
            370,
            self.PREF_TOGGLE_H,
        )
        self.adaptive_desc_rect = pygame.Rect(
            self.pref_panel_rect.x + 26,
            self.pref_panel_rect.y + self.PREF_ROW1_Y + 60,
            self.pref_panel_rect.width - 52,
            18,
        )

        total_button_width = self.ACTION_BUTTON_W * 3 + self.ACTION_BUTTON_GAP * 2
        button_start_x = self.width // 2 - total_button_width // 2
        button_y = offset_y + self.ACTION_BUTTON_Y
        self.start_button_rect = pygame.Rect(button_start_x, button_y, self.ACTION_BUTTON_W, self.ACTION_BUTTON_H)
        self.save_back_button_rect = pygame.Rect(
            button_start_x + self.ACTION_BUTTON_W + self.ACTION_BUTTON_GAP,
            button_y,
            self.ACTION_BUTTON_W,
            self.ACTION_BUTTON_H,
        )
        self.cancel_button_rect = pygame.Rect(
            button_start_x + (self.ACTION_BUTTON_W + self.ACTION_BUTTON_GAP) * 2,
            button_y,
            self.ACTION_BUTTON_W,
            self.ACTION_BUTTON_H,
        )

    def _reflow_layout(self):
        self.layout_offset_x = max(0, (self.width - self.BASE_WIDTH) // 2)
        self.layout_offset_y = max(0, (self.height - self.BASE_HEIGHT) // 2)
        self._create_ui_elements()

    def on_resize(self, width, height):
        self.width = width
        self.height = height
        self._reflow_layout()

    def _commit_settings(self):
        self.manager.settings["start_level"] = self.draft_settings["start_level"]
        self.manager.settings["total_questions"] = self.draft_settings["total_questions"]
        self.manager.settings["adaptive_enabled"] = self.draft_settings["adaptive_enabled"]
        self.manager.save_user_preferences()
        self.original_settings = dict(self.draft_settings)
        self._set_feedback("config.feedback_saved", "success")

    def _commit_if_valid(self):
        if not self._validate_and_update_questions(allow_empty=False):
            return False
        self._commit_settings()
        return True

    def _cancel_changes(self):
        if not self.original_settings:
            self.manager.set_scene(self._return_scene_name())
            return
        self.manager.settings.update(self.original_settings)
        self.draft_settings = dict(self.original_settings)
        self.input_text = str(self.draft_settings["total_questions"])
        self._set_feedback("config.feedback_canceled", "warning")
        self.manager.set_scene(self._return_scene_name())

    def _set_level(self, level):
        if self.draft_settings["start_level"] != level:
            self.draft_settings["start_level"] = level
            self.level_flash_level = level
            self.level_flash_frames = 14

    def _adjust_questions(self, delta):
        self._validate_and_update_questions(allow_empty=False)
        next_value = self.draft_settings["total_questions"] + delta
        self.draft_settings["total_questions"] = max(MIN_QUESTIONS, min(MAX_QUESTIONS, next_value))
        self.input_text = str(self.draft_settings["total_questions"])
        self.input_error = ""

    def _validate_and_update_questions(self, allow_empty=True):
        raw = self.input_text.strip()
        if raw == "":
            if allow_empty:
                self.input_error = self.manager.t("config.input_error_empty")
                self._set_feedback("config.input_error_empty", "error")
                return False
            raw = "0"

        if not raw.isdigit():
            self.input_error = self.manager.t("config.input_error_digits")
            self._set_feedback("config.input_error_digits", "error")
            return False

        value = int(raw)
        if value < MIN_QUESTIONS or value > MAX_QUESTIONS:
            self.input_error = self.manager.t(
                "config.input_error_range",
                min_questions=MIN_QUESTIONS,
                max_questions=MAX_QUESTIONS,
            )
            self._set_feedback(
                "config.input_error_range",
                "error",
                min_questions=MIN_QUESTIONS,
                max_questions=MAX_QUESTIONS,
            )
            return False

        self.draft_settings["total_questions"] = value
        self.input_text = str(value)
        self.input_error = ""
        return True

    def handle_events(self, events):
        mouse_pos = pygame.mouse.get_pos()
        self.hovered_level = None
        for rect, level in self.level_cards:
            if rect.collidepoint(mouse_pos):
                self.hovered_level = level
                break

        for event in events:
            if event.type == pygame.KEYDOWN:
                if self.input_active:
                    if event.key == pygame.K_RETURN:
                        self.input_active = False
                        self._validate_and_update_questions(allow_empty=True)
                        continue
                    if event.key == pygame.K_BACKSPACE:
                        self.input_text = self.input_text[:-1]
                        self._validate_and_update_questions(allow_empty=True)
                        continue
                    if event.unicode.isdigit() and len(self.input_text) < 4:
                        self.input_text += event.unicode
                        self._validate_and_update_questions(allow_empty=True)
                    elif event.unicode and not event.unicode.isspace():
                        self.input_error = self.manager.t("config.input_error_digits")
                        self._set_feedback("config.input_error_digits", "error")
                    continue

                if event.key == pygame.K_ESCAPE:
                    self._cancel_changes()
                elif event.key == pygame.K_RETURN:
                    if self._commit_if_valid():
                        self.manager.set_scene("training")
                elif event.key == pygame.K_s:
                    if event.mod & pygame.KMOD_CTRL:
                        if self._commit_if_valid():
                            self.manager.set_scene(self._return_scene_name())
                elif event.key == pygame.K_a:
                    self.draft_settings["adaptive_enabled"] = not self.draft_settings["adaptive_enabled"]
                elif event.key == pygame.K_UP:
                    self._set_level(max(1, self.draft_settings["start_level"] - 1))
                elif event.key == pygame.K_DOWN:
                    self._set_level(min(len(E_SIZE_LEVELS), self.draft_settings["start_level"] + 1))

            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                clicked_input = self.input_rect.collidepoint(mouse_pos)
                if self.input_active and not clicked_input:
                    self.input_active = False
                    self._validate_and_update_questions(allow_empty=True)
                self.input_active = clicked_input

                for rect, level in self.level_cards:
                    if rect.collidepoint(mouse_pos):
                        self._set_level(level)
                        break

                if self.minus_button_rect.collidepoint(mouse_pos):
                    self._adjust_questions(-1)
                elif self.plus_button_rect.collidepoint(mouse_pos):
                    self._adjust_questions(1)

                if self.start_button_rect.collidepoint(mouse_pos):
                    if self._commit_if_valid():
                        self.manager.set_scene("training")
                elif self.save_back_button_rect.collidepoint(mouse_pos):
                    if self._commit_if_valid():
                        self.manager.set_scene(self._return_scene_name())
                elif self.cancel_button_rect.collidepoint(mouse_pos):
                    self._cancel_changes()
                elif self.adaptive_toggle_rect.collidepoint(mouse_pos):
                    if mouse_pos[0] < self.adaptive_toggle_rect.centerx:
                        self.draft_settings["adaptive_enabled"] = True
                    else:
                        self.draft_settings["adaptive_enabled"] = False

    def _draw_panel(self, screen, rect, title, mouse_pos):
        hovered = rect.collidepoint(mouse_pos)
        draw_card(screen, rect, hovered=hovered, alt=True, radius=self.PANEL_RADIUS)
        title_surface = self.subtitle_font.render(title, True, PlatformTheme.TEXT_PRIMARY)
        screen.blit(title_surface, (rect.x + 16, rect.y + 12))

    def _draw_segmented_control(self, screen, rect, label, left_text, right_text, left_selected, mouse_pos):
        hovered = rect.collidepoint(mouse_pos)
        # 统一分段开关语义：底板 + 选中胶囊 + 未选中暗底
        bg = (230, 220, 203) if hovered else (237, 229, 214)
        pygame.draw.rect(screen, bg, rect, border_radius=self.CONTROL_RADIUS + 2)
        pygame.draw.rect(screen, PlatformTheme.BORDER_HOVER if hovered else PlatformTheme.BORDER, rect, 2, border_radius=self.CONTROL_RADIUS + 2)

        left_rect = pygame.Rect(rect.x + 2, rect.y + 2, rect.width // 2 - 3, rect.height - 4)
        right_rect = pygame.Rect(rect.centerx + 1, rect.y + 2, rect.width // 2 - 3, rect.height - 4)

        if left_selected:
            pygame.draw.rect(screen, (137, 187, 112), left_rect, border_radius=self.CONTROL_RADIUS)
            pygame.draw.rect(screen, (190, 225, 171), left_rect, 1, border_radius=self.CONTROL_RADIUS)
            pygame.draw.rect(screen, (214, 205, 191), right_rect, border_radius=self.CONTROL_RADIUS)
            left_color = (255, 255, 255)
            right_color = PlatformTheme.TEXT_MUTED
        else:
            pygame.draw.rect(screen, (214, 205, 191), left_rect, border_radius=self.CONTROL_RADIUS)
            pygame.draw.rect(screen, (238, 174, 97), right_rect, border_radius=self.CONTROL_RADIUS)
            pygame.draw.rect(screen, (255, 224, 177), right_rect, 1, border_radius=self.CONTROL_RADIUS)
            left_color = PlatformTheme.TEXT_MUTED
            right_color = (255, 255, 255)

        if label:
            label_surface = self.small_font.render(label, True, PlatformTheme.TEXT_MUTED)
            screen.blit(label_surface, (rect.x, rect.y - 22))

        left_surface = self.small_font.render(left_text, True, left_color)
        right_surface = self.small_font.render(right_text, True, right_color)
        screen.blit(
            left_surface,
            (left_rect.centerx - left_surface.get_width() // 2, left_rect.centery - left_surface.get_height() // 2),
        )
        screen.blit(
            right_surface,
            (right_rect.centerx - right_surface.get_width() // 2, right_rect.centery - right_surface.get_height() // 2),
        )

    def _draw_action_button(self, screen, rect, text, mouse_pos, variant):
        hovered = rect.collidepoint(mouse_pos)
        if variant == "primary":
            base = (137, 187, 112)
            border = (190, 225, 171)
            text_color = (255, 255, 255)
        elif variant == "secondary":
            base = PlatformTheme.ACCENT
            border = (255, 224, 177)
            text_color = (255, 250, 244)
        else:
            base = (214, 205, 191)
            border = PlatformTheme.BORDER
            text_color = PlatformTheme.TEXT_PRIMARY

        if hovered:
            fill = tuple(min(c + 24, 255) for c in base)
        else:
            fill = base

        pygame.draw.rect(screen, fill, rect, border_radius=self.BUTTON_RADIUS)
        pygame.draw.rect(screen, border, rect, 2, border_radius=self.BUTTON_RADIUS)
        txt = self.font.render(text, True, text_color)
        screen.blit(txt, (rect.centerx - txt.get_width() // 2, rect.centery - txt.get_height() // 2))

    def _draw_feedback(self, screen):
        if not self.feedback_message:
            return
        if self.feedback_variant == "success":
            fill = (223, 242, 214)
            border = (148, 198, 124)
            color = (73, 113, 61)
        elif self.feedback_variant == "warning":
            fill = (255, 241, 209)
            border = (226, 190, 105)
            color = (130, 98, 39)
        elif self.feedback_variant == "error":
            fill = (252, 225, 225)
            border = (226, 151, 151)
            color = (138, 75, 75)
        else:
            fill = (230, 240, 247)
            border = (150, 182, 205)
            color = (78, 104, 126)

        fb_rect = pygame.Rect(self.width // 2 - 270, self.layout_offset_y + 510, 540, 28)
        pygame.draw.rect(screen, fill, fb_rect, border_radius=self.CONTROL_RADIUS)
        pygame.draw.rect(screen, border, fb_rect, 2, border_radius=self.CONTROL_RADIUS)
        fb_text = self._fit_text(self.feedback_message, self.tiny_font, fb_rect.width - 16)
        fb_surf = self.tiny_font.render(fb_text, True, color)
        screen.blit(fb_surf, (fb_rect.centerx - fb_surf.get_width() // 2, fb_rect.centery - fb_surf.get_height() // 2))

    def _draw_tooltip(self, screen, text, mouse_pos):
        text_surf = self.tiny_font.render(text, True, PlatformTheme.TEXT_PRIMARY)
        pad_x = 10
        pad_y = 6
        tip_w = text_surf.get_width() + pad_x * 2
        tip_h = text_surf.get_height() + pad_y * 2

        tip_x = mouse_pos[0] + 14
        tip_y = mouse_pos[1] - tip_h - 12
        if tip_x + tip_w > self.width - 8:
            tip_x = self.width - tip_w - 8
        if tip_x < 8:
            tip_x = 8
        if tip_y < 8:
            tip_y = mouse_pos[1] + 14
        if tip_y + tip_h > self.height - 8:
            tip_y = self.height - tip_h - 8

        tip_rect = pygame.Rect(tip_x, tip_y, tip_w, tip_h)
        pygame.draw.rect(screen, (255, 249, 238), tip_rect, border_radius=7)
        pygame.draw.rect(screen, PlatformTheme.BORDER_HOVER, tip_rect, 2, border_radius=7)
        screen.blit(text_surf, (tip_rect.x + pad_x, tip_rect.y + pad_y))

    def draw(self, screen):
        self.refresh_fonts_if_needed()
        draw_platform_background(screen, self.width, self.height)
        mouse_pos = pygame.mouse.get_pos()

        title = self.title_font.render(self.manager.t("config.title"), True, PlatformTheme.TEXT_PRIMARY)
        screen.blit(title, (self.width // 2 - title.get_width() // 2, self.title_y))
        info_text = self._fit_text(self.manager.t("config.info"), self.tiny_font, self.width - 120)
        info = self.tiny_font.render(info_text, True, PlatformTheme.TEXT_MUTED)
        screen.blit(info, (self.width // 2 - info.get_width() // 2, self.info_y))

        self._draw_panel(screen, self.level_panel_rect, self.manager.t("config.difficulty_level"), mouse_pos)
        self._draw_panel(screen, self.preview_panel_rect, self.manager.t("config.font_preview"), mouse_pos)
        self._draw_panel(screen, self.question_panel_rect, self.manager.t("config.question_count"), mouse_pos)
        self._draw_panel(screen, self.pref_panel_rect, self.manager.t("config.section_preferences"), mouse_pos)

        # 难度分组背景（10级模式）
        for group in getattr(self, "level_groups", []):
            group_rect = group["rect"]
            pygame.draw.rect(screen, (244, 239, 232), group_rect, border_radius=self.BUTTON_RADIUS)
            pygame.draw.rect(screen, PlatformTheme.BORDER, group_rect, 1, border_radius=self.BUTTON_RADIUS)
            group_title = self.tiny_font.render(self.manager.t(group["title_key"]), True, PlatformTheme.TEXT_MUTED)
            screen.blit(group_title, (group_rect.centerx - group_title.get_width() // 2, group_rect.y + 6))

        # 难度卡
        compact = len(E_SIZE_LEVELS) > 8
        level_font = self.small_font if compact else self.font
        size_font = self.create_font(14) if compact else self.small_font
        for rect, level in self.level_cards:
            size_value = E_SIZE_LEVELS[level - 1]
            selected = level == self.draft_settings["start_level"]
            hovered = rect.collidepoint(mouse_pos)
            if selected:
                fill = PlatformTheme.ACCENT
                border = (255, 224, 177)
            elif hovered:
                fill = PlatformTheme.CARD_HOVER
                border = PlatformTheme.BORDER_HOVER
            else:
                fill = PlatformTheme.CARD_ALT
                border = PlatformTheme.BORDER
            pygame.draw.rect(screen, fill, rect, border_radius=self.CONTROL_RADIUS)
            pygame.draw.rect(screen, border, rect, 2, border_radius=self.CONTROL_RADIUS)

            if self.level_flash_frames > 0 and level == self.level_flash_level:
                pygame.draw.rect(screen, (245, 225, 130), rect.inflate(4, 4), 2, border_radius=10)

            if rect.height <= 30:
                one_line = self.tiny_font.render(f"L{level}  {size_value}px", True, PlatformTheme.TEXT_PRIMARY)
                screen.blit(
                    one_line,
                    (
                        rect.centerx - one_line.get_width() // 2,
                        rect.centery - one_line.get_height() // 2,
                    ),
                )
            else:
                ltxt = level_font.render(f"L{level}", True, PlatformTheme.TEXT_PRIMARY)
                stxt = size_font.render(f"{size_value}px", True, PlatformTheme.TEXT_MUTED)
                if compact:
                    ltxt_y = rect.y + 2
                    stxt_y = rect.y + 22
                else:
                    ltxt_y = rect.y + 5
                    stxt_y = rect.y + 29
                screen.blit(ltxt, (rect.centerx - ltxt.get_width() // 2, ltxt_y))
                screen.blit(stxt, (rect.centerx - stxt.get_width() // 2, stxt_y))

        # 预览信息
        preview_level = self.hovered_level if self.hovered_level is not None else self.draft_settings["start_level"]
        preview_size = E_SIZE_LEVELS[preview_level - 1]
        distance = max(1.0, round(4.5 - (preview_level - 1) * 0.5, 1))
        preview_surface = EGenerator.create_e_surface(preview_size, "RIGHT")
        preview_surface.fill((0, 0, 0), special_flags=pygame.BLEND_RGB_MULT)
        preview_rect = preview_surface.get_rect(center=(self.preview_panel_rect.centerx, self.preview_panel_rect.y + 100))
        screen.blit(preview_surface, preview_rect)

        info1 = self.small_font.render(
            self.manager.t("config.preview_level_size", level=preview_level, size=preview_size),
            True,
            PlatformTheme.TEXT_PRIMARY,
        )
        screen.blit(info1, (self.preview_panel_rect.x + 20, self.preview_panel_rect.y + 150))

        if self.hovered_level is not None:
            info2_text = self.manager.t("config.preview_hover_tip", level=self.hovered_level)
        else:
            info2_text = self.manager.t(
                "config.preview_recommend",
                distance=f"{distance:.1f}",
            )
        info2 = self.small_font.render(info2_text, True, PlatformTheme.TEXT_MUTED)
        screen.blit(info2, (self.preview_panel_rect.x + 20, self.preview_panel_rect.y + 176))

        # 题量输入
        range_text = self.small_font.render(
            self.manager.t("config.range", min_questions=MIN_QUESTIONS, max_questions=MAX_QUESTIONS),
            True,
            PlatformTheme.TEXT_MUTED,
        )
        screen.blit(range_text, (self.question_panel_rect.x + 26, self.question_panel_rect.y + 42))

        adjust_text = self.small_font.render(self.manager.t("config.adjust_hint"), True, PlatformTheme.TEXT_MUTED)
        screen.blit(adjust_text, (self.question_panel_rect.x + 26, self.question_panel_rect.y + 122))

        input_fill = (255, 251, 245) if self.input_active else (240, 235, 226)
        border = PlatformTheme.BORDER_HOVER if self.input_active else PlatformTheme.BORDER
        pygame.draw.rect(screen, input_fill, self.input_rect, border_radius=self.CONTROL_RADIUS)
        pygame.draw.rect(screen, border, self.input_rect, 2, border_radius=self.CONTROL_RADIUS)

        val = self.font.render(self.input_text, True, PlatformTheme.TEXT_PRIMARY)
        screen.blit(val, (self.input_rect.centerx - val.get_width() // 2, self.input_rect.centery - val.get_height() // 2))

        for rect, symbol in ((self.minus_button_rect, "-"), (self.plus_button_rect, "+")):
            hovered = rect.collidepoint(mouse_pos)
            fill = (239, 181, 111) if hovered else (230, 220, 203)
            pygame.draw.rect(screen, fill, rect, border_radius=self.CONTROL_RADIUS)
            pygame.draw.rect(screen, PlatformTheme.BORDER_HOVER if hovered else PlatformTheme.BORDER, rect, 2, border_radius=self.CONTROL_RADIUS)
            sym = self.subtitle_font.render(symbol, True, PlatformTheme.TEXT_PRIMARY)
            screen.blit(sym, (rect.centerx - sym.get_width() // 2, rect.centery - sym.get_height() // 2))

        if self.input_error:
            err = self.tiny_font.render(self.input_error, True, (180, 98, 98))
            screen.blit(err, (self.question_panel_rect.x + 26, self.question_panel_rect.y + 146))

        # 偏好分段开关（仅自适应）
        self._draw_segmented_control(
            screen,
            self.adaptive_toggle_rect,
            self.manager.t("config.adaptive_label"),
            self.manager.t("config.on"),
            self.manager.t("config.off"),
            self.draft_settings["adaptive_enabled"],
            mouse_pos,
        )
        adaptive_short = self.manager.t("config.adaptive_desc_short")
        adaptive_desc = self.tiny_font.render(adaptive_short, True, PlatformTheme.TEXT_MUTED)
        screen.blit(adaptive_desc, (self.adaptive_desc_rect.x, self.adaptive_desc_rect.y))

        if self.adaptive_desc_rect.collidepoint(mouse_pos) or self.adaptive_toggle_rect.collidepoint(mouse_pos):
            self._draw_tooltip(screen, self.manager.t("config.adaptive_desc"), mouse_pos)

        # 底部状态与按钮
        current_size = E_SIZE_LEVELS[self.draft_settings["start_level"] - 1]
        status_text = self.manager.t(
            "config.status",
            level=self.draft_settings["start_level"],
            size=current_size,
            questions=self.draft_settings["total_questions"],
        )
        status = self.small_font.render(status_text, True, (184, 220, 178))
        screen.blit(status, (self.width // 2 - status.get_width() // 2, self.layout_offset_y + 540))
        if self.feedback_frames > 0:
            self._draw_feedback(screen)

        for rect, text, variant in (
            (self.start_button_rect, self.manager.t("config.start_game"), "primary"),
            (self.save_back_button_rect, self.manager.t("config.save_back"), "secondary"),
            (self.cancel_button_rect, self.manager.t("config.cancel"), "tertiary"),
        ):
            self._draw_action_button(screen, rect, text, mouse_pos, variant)
