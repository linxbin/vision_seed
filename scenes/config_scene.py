import pygame
from core.base_scene import BaseScene
from core.e_generator import EGenerator
from config import E_SIZE_LEVELS, SCREEN_WIDTH, MIN_QUESTIONS, MAX_QUESTIONS


class ConfigScene(BaseScene):
    def __init__(self, manager):
        super().__init__(manager)
        self._refresh_fonts()
        self.e_generator = EGenerator()

        self.width = SCREEN_WIDTH
        self.height = 700
        self.layout_offset_x = 0
        self.layout_offset_y = 0

        self.current_level = self.manager.settings["start_level"]
        self.current_questions = self.manager.settings["total_questions"]
        self.current_sound_enabled = self.manager.settings.get("sound_enabled", True)
        self.current_language = self.manager.settings.get("language", "en-US")

        self.input_active = False
        self.input_text = str(self.current_questions)
        self.input_error = ""

        self.hovered_level = None
        self.level_flash_frames = 0
        self.level_flash_level = self.current_level

        self.level_cards = []
        self._reflow_layout()

    def _refresh_fonts(self):
        self.font = self.create_font(24)
        self.title_font = self.create_font(36)
        self.subtitle_font = self.create_font(26)
        self.small_font = self.create_font(18)

    def on_enter(self):
        self.current_level = self.manager.settings["start_level"]
        self.current_questions = self.manager.settings["total_questions"]
        self.current_sound_enabled = self.manager.settings.get("sound_enabled", True)
        self.current_language = self.manager.settings.get("language", "en-US")
        self.input_text = str(self.current_questions)
        self.input_error = ""
        self.input_active = False

    def update(self):
        if self.level_flash_frames > 0:
            self.level_flash_frames -= 1

    def _create_ui_elements(self):
        offset_x = self.layout_offset_x
        offset_y = self.layout_offset_y

        self.title_y = offset_y + 28
        self.info_y = offset_y + 66

        self.level_panel_rect = pygame.Rect(offset_x + 40, offset_y + 105, 380, 235)
        self.preview_panel_rect = pygame.Rect(offset_x + 440, offset_y + 105, 420, 235)
        self.question_panel_rect = pygame.Rect(offset_x + 40, offset_y + 355, 380, 170)
        self.pref_panel_rect = pygame.Rect(offset_x + 440, offset_y + 355, 420, 170)

        level_count = len(E_SIZE_LEVELS)
        compact = level_count > 8
        columns = 5 if compact else 4
        card_w = 62 if compact else 78
        card_h = 42 if compact else 52
        card_gap = 8 if compact else 12
        start_x = self.level_panel_rect.x + 18
        start_y = self.level_panel_rect.y + 58
        self.level_cards = []
        for i in range(level_count):
            row = i // columns
            col = i % columns
            x = start_x + col * (card_w + card_gap)
            y = start_y + row * (card_h + card_gap)
            self.level_cards.append((pygame.Rect(x, y, card_w, card_h), i + 1))

        self.input_rect = pygame.Rect(self.question_panel_rect.x + 30, self.question_panel_rect.y + 76, 140, 40)
        self.minus_button_rect = pygame.Rect(self.input_rect.right + 14, self.input_rect.y, 40, 40)
        self.plus_button_rect = pygame.Rect(self.minus_button_rect.right + 10, self.input_rect.y, 40, 40)

        self.sound_toggle_rect = pygame.Rect(self.pref_panel_rect.x + 25, self.pref_panel_rect.y + 60, 180, 42)
        self.language_toggle_rect = pygame.Rect(self.pref_panel_rect.x + 215, self.pref_panel_rect.y + 60, 180, 42)

        self.start_button_rect = pygame.Rect(self.width // 2 - 145, offset_y + 560, 130, 42)
        self.back_button_rect = pygame.Rect(self.width // 2 + 15, offset_y + 560, 130, 42)

    def _reflow_layout(self):
        base_width = SCREEN_WIDTH
        base_height = 700
        self.layout_offset_x = max(0, (self.width - base_width) // 2)
        self.layout_offset_y = max(0, (self.height - base_height) // 2)
        self._create_ui_elements()

    def on_resize(self, width, height):
        self.width = width
        self.height = height
        self._reflow_layout()

    def _commit_settings(self):
        self.manager.settings["start_level"] = self.current_level
        self.manager.settings["total_questions"] = self.current_questions
        self.manager.settings["sound_enabled"] = self.current_sound_enabled
        self.manager.settings["language"] = self.current_language
        self.manager.apply_language_preference()
        self.manager.apply_sound_preference()
        self.manager.save_user_preferences()

    def _apply_live_preferences(self):
        """即时应用语言/音效，保持配置界面所见即所得。"""
        self.manager.settings["language"] = self.current_language
        self.manager.settings["sound_enabled"] = self.current_sound_enabled
        self.manager.apply_language_preference()
        self.manager.apply_sound_preference()

    def _toggle_language(self):
        self.current_language = "zh-CN" if self.current_language == "en-US" else "en-US"

    def _set_level(self, level):
        if self.current_level != level:
            self.current_level = level
            self.level_flash_level = level
            self.level_flash_frames = 14

    def _adjust_questions(self, delta):
        self._validate_and_update_questions(allow_empty=False)
        self.current_questions = max(MIN_QUESTIONS, min(MAX_QUESTIONS, self.current_questions + delta))
        self.input_text = str(self.current_questions)
        self.input_error = ""

    def _validate_and_update_questions(self, allow_empty=True):
        raw = self.input_text.strip()
        if raw == "":
            if allow_empty:
                self.input_error = self.manager.t("config.input_error_empty")
                return False
            raw = "0"

        if not raw.isdigit():
            self.input_error = self.manager.t("config.input_error_digits")
            return False

        value = int(raw)
        if value < MIN_QUESTIONS or value > MAX_QUESTIONS:
            self.input_error = self.manager.t(
                "config.input_error_range",
                min_questions=MIN_QUESTIONS,
                max_questions=MAX_QUESTIONS,
            )
            return False

        self.current_questions = value
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
                    continue

                if event.key == pygame.K_ESCAPE:
                    self._validate_and_update_questions(allow_empty=False)
                    self._commit_settings()
                    self.manager.set_scene("menu")
                elif event.key == pygame.K_RETURN:
                    self._validate_and_update_questions(allow_empty=False)
                    self._commit_settings()
                    self.manager.set_scene("training")
                elif event.key == pygame.K_m:
                    self.current_sound_enabled = not self.current_sound_enabled
                    self._apply_live_preferences()
                elif event.key == pygame.K_l:
                    self._toggle_language()
                    self._apply_live_preferences()
                elif event.key == pygame.K_UP:
                    self._set_level(max(1, self.current_level - 1))
                elif event.key == pygame.K_DOWN:
                    self._set_level(min(len(E_SIZE_LEVELS), self.current_level + 1))

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
                    self._validate_and_update_questions(allow_empty=False)
                    self._commit_settings()
                    self.manager.set_scene("training")
                elif self.back_button_rect.collidepoint(mouse_pos):
                    self._validate_and_update_questions(allow_empty=False)
                    self._commit_settings()
                    self.manager.set_scene("menu")
                elif self.sound_toggle_rect.collidepoint(mouse_pos):
                    if mouse_pos[0] < self.sound_toggle_rect.centerx:
                        self.current_sound_enabled = True
                    else:
                        self.current_sound_enabled = False
                    self._apply_live_preferences()
                elif self.language_toggle_rect.collidepoint(mouse_pos):
                    if mouse_pos[0] < self.language_toggle_rect.centerx:
                        self.current_language = "en-US"
                    else:
                        self.current_language = "zh-CN"
                    self._apply_live_preferences()

    def _draw_panel(self, screen, rect, title, mouse_pos):
        hovered = rect.collidepoint(mouse_pos)
        fill = (40, 56, 90) if hovered else (34, 48, 78)
        border = (110, 145, 205) if hovered else (86, 116, 170)
        pygame.draw.rect(screen, fill, rect, border_radius=12)
        pygame.draw.rect(screen, border, rect, 2, border_radius=12)

        title_surface = self.subtitle_font.render(title, True, (235, 240, 255))
        screen.blit(title_surface, (rect.x + 16, rect.y + 14))

    def _draw_segmented_control(self, screen, rect, label, left_text, right_text, left_selected, mouse_pos):
        hovered = rect.collidepoint(mouse_pos)
        bg = (56, 78, 124) if hovered else (46, 66, 108)
        pygame.draw.rect(screen, bg, rect, border_radius=10)
        pygame.draw.rect(screen, (165, 192, 235), rect, 2, border_radius=10)

        left_rect = pygame.Rect(rect.x + 2, rect.y + 2, rect.width // 2 - 3, rect.height - 4)
        right_rect = pygame.Rect(rect.centerx + 1, rect.y + 2, rect.width // 2 - 3, rect.height - 4)

        if left_selected:
            pygame.draw.rect(screen, (70, 160, 98), left_rect, border_radius=8)
            pygame.draw.rect(screen, (136, 214, 160), left_rect, 1, border_radius=8)
            pygame.draw.rect(screen, (80, 94, 124), right_rect, border_radius=8)
        else:
            pygame.draw.rect(screen, (80, 94, 124), left_rect, border_radius=8)
            pygame.draw.rect(screen, (82, 126, 182), right_rect, border_radius=8)
            pygame.draw.rect(screen, (146, 188, 240), right_rect, 1, border_radius=8)

        label_surface = self.small_font.render(label, True, (205, 220, 245))
        screen.blit(label_surface, (rect.x, rect.y - 24))

        left_surface = self.small_font.render(left_text, True, (255, 255, 255))
        right_surface = self.small_font.render(right_text, True, (255, 255, 255))
        screen.blit(
            left_surface,
            (left_rect.centerx - left_surface.get_width() // 2, left_rect.centery - left_surface.get_height() // 2),
        )
        screen.blit(
            right_surface,
            (right_rect.centerx - right_surface.get_width() // 2, right_rect.centery - right_surface.get_height() // 2),
        )

    def draw(self, screen):
        self._refresh_fonts()
        screen.fill((24, 34, 58))
        mouse_pos = pygame.mouse.get_pos()

        title = self.title_font.render(self.manager.t("config.title"), True, (255, 255, 255))
        screen.blit(title, (self.width // 2 - title.get_width() // 2, self.title_y))
        info = self.small_font.render(self.manager.t("config.info"), True, (176, 190, 220))
        screen.blit(info, (self.width // 2 - info.get_width() // 2, self.info_y))

        self._draw_panel(screen, self.level_panel_rect, self.manager.t("config.difficulty_level"), mouse_pos)
        self._draw_panel(screen, self.preview_panel_rect, self.manager.t("config.font_preview"), mouse_pos)
        self._draw_panel(screen, self.question_panel_rect, self.manager.t("config.question_count"), mouse_pos)
        self._draw_panel(screen, self.pref_panel_rect, self.manager.t("config.section_preferences"), mouse_pos)

        # 难度卡
        compact = len(E_SIZE_LEVELS) > 8
        level_font = self.small_font if compact else self.font
        size_font = self.create_font(14) if compact else self.small_font
        for rect, level in self.level_cards:
            size_value = E_SIZE_LEVELS[level - 1]
            selected = level == self.current_level
            hovered = rect.collidepoint(mouse_pos)
            if selected:
                fill = (80, 128, 206)
                border = (178, 208, 255)
            elif hovered:
                fill = (68, 102, 170)
                border = (140, 172, 228)
            else:
                fill = (56, 76, 120)
                border = (96, 124, 176)
            pygame.draw.rect(screen, fill, rect, border_radius=8)
            pygame.draw.rect(screen, border, rect, 2, border_radius=8)

            if self.level_flash_frames > 0 and level == self.level_flash_level:
                pygame.draw.rect(screen, (245, 225, 130), rect.inflate(4, 4), 2, border_radius=10)

            ltxt = level_font.render(f"L{level}", True, (255, 255, 255))
            stxt = size_font.render(f"{size_value}px", True, (224, 230, 242))
            if compact:
                ltxt_y = rect.y + 2
                stxt_y = rect.y + 22
            else:
                ltxt_y = rect.y + 5
                stxt_y = rect.y + 29
            screen.blit(ltxt, (rect.centerx - ltxt.get_width() // 2, ltxt_y))
            screen.blit(stxt, (rect.centerx - stxt.get_width() // 2, stxt_y))

        # 预览信息
        preview_level = self.hovered_level if self.hovered_level is not None else self.current_level
        preview_size = E_SIZE_LEVELS[preview_level - 1]
        distance = max(1.0, round(4.5 - (preview_level - 1) * 0.5, 1))
        self.e_generator.draw_e(
            screen,
            (self.preview_panel_rect.centerx, self.preview_panel_rect.y + 100),
            preview_size,
            "RIGHT",
        )

        info1 = self.small_font.render(
            self.manager.t("config.preview_level_size", level=preview_level, size=preview_size),
            True,
            (220, 230, 245),
        )
        screen.blit(info1, (self.preview_panel_rect.x + 20, self.preview_panel_rect.y + 150))

        if self.hovered_level is not None:
            info2_text = self.manager.t("config.preview_hover_tip", level=self.hovered_level)
        else:
            info2_text = self.manager.t(
                "config.preview_recommend",
                distance=f"{distance:.1f}",
            )
        info2 = self.small_font.render(info2_text, True, (182, 205, 236))
        screen.blit(info2, (self.preview_panel_rect.x + 20, self.preview_panel_rect.y + 176))

        # 题量输入
        range_text = self.small_font.render(
            self.manager.t("config.range", min_questions=MIN_QUESTIONS, max_questions=MAX_QUESTIONS),
            True,
            (186, 202, 230),
        )
        screen.blit(range_text, (self.question_panel_rect.x + 26, self.question_panel_rect.y + 42))

        adjust_text = self.small_font.render(self.manager.t("config.adjust_hint"), True, (162, 183, 215))
        screen.blit(adjust_text, (self.question_panel_rect.x + 26, self.question_panel_rect.y + 122))

        input_fill = (210, 226, 245) if self.input_active else (183, 202, 230)
        border = (122, 162, 220) if self.input_active else (95, 130, 184)
        pygame.draw.rect(screen, input_fill, self.input_rect, border_radius=8)
        pygame.draw.rect(screen, border, self.input_rect, 2, border_radius=8)

        val = self.font.render(self.input_text, True, (18, 26, 40))
        screen.blit(val, (self.input_rect.centerx - val.get_width() // 2, self.input_rect.centery - val.get_height() // 2))

        for rect, symbol in ((self.minus_button_rect, "-"), (self.plus_button_rect, "+")):
            hovered = rect.collidepoint(mouse_pos)
            fill = (76, 112, 170) if hovered else (64, 94, 144)
            pygame.draw.rect(screen, fill, rect, border_radius=8)
            pygame.draw.rect(screen, (146, 178, 232), rect, 2, border_radius=8)
            sym = self.subtitle_font.render(symbol, True, (240, 245, 255))
            screen.blit(sym, (rect.centerx - sym.get_width() // 2, rect.centery - sym.get_height() // 2))

        if self.input_error:
            err = self.small_font.render(self.input_error, True, (245, 138, 138))
            screen.blit(err, (self.question_panel_rect.x + 26, self.question_panel_rect.y + 146))

        # 偏好分段开关
        self._draw_segmented_control(
            screen,
            self.sound_toggle_rect,
            self.manager.t("config.sound_label"),
            self.manager.t("config.on"),
            self.manager.t("config.off"),
            self.current_sound_enabled,
            mouse_pos,
        )
        self._draw_segmented_control(
            screen,
            self.language_toggle_rect,
            self.manager.t("config.lang_label"),
            self.manager.t("config.lang_en"),
            self.manager.t("config.lang_zh"),
            self.current_language == "en-US",
            mouse_pos,
        )

        # 底部状态与按钮
        current_size = E_SIZE_LEVELS[self.current_level - 1]
        status_text = self.manager.t(
            "config.status",
            level=self.current_level,
            size=current_size,
            questions=self.current_questions,
        )
        status = self.small_font.render(status_text, True, (184, 220, 178))
        screen.blit(status, (self.width // 2 - status.get_width() // 2, self.layout_offset_y + 540))

        for rect, text, base in (
            (self.start_button_rect, self.manager.t("config.start_game"), (62, 155, 90)),
            (self.back_button_rect, self.manager.t("config.back"), (88, 108, 150)),
        ):
            hovered = rect.collidepoint(mouse_pos)
            fill = tuple(min(c + 22, 255) for c in base) if hovered else base
            pygame.draw.rect(screen, fill, rect, border_radius=9)
            pygame.draw.rect(screen, (185, 205, 235), rect, 2, border_radius=9)
            txt = self.font.render(text, True, (255, 255, 255))
            screen.blit(txt, (rect.centerx - txt.get_width() // 2, rect.centery - txt.get_height() // 2))
