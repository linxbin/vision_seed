import pygame
from core.base_scene import BaseScene
from core.e_generator import EGenerator
from config import E_SIZE_LEVELS, SCREEN_WIDTH, SCREEN_HEIGHT, MIN_QUESTIONS, MAX_QUESTIONS


class ConfigScene(BaseScene):
    """配置场景 - 按照用户建议重新设计布局"""

    def __init__(self, manager):
        super().__init__(manager)
        self._refresh_fonts()
        self.e_generator = EGenerator()
        
        # 初始化当前选中的设置（从settings中读取）
        self.current_level = self.manager.settings["start_level"]
        self.current_questions = self.manager.settings["total_questions"]
        self.current_sound_enabled = self.manager.settings.get("sound_enabled", True)
        self.current_language = self.manager.settings.get("language", "en-US")
        
        # 确保当前题目数量在有效范围内 (0-1000)
        if self.current_questions < MIN_QUESTIONS:
            self.current_questions = MIN_QUESTIONS
        elif self.current_questions > MAX_QUESTIONS:
            self.current_questions = MAX_QUESTIONS
        
        # 输入框相关变量
        self.input_active = False
        self.input_text = str(self.current_questions)
        
        # UI元素矩形区域
        self.level_cards = []  # 存储等级卡片的矩形区域
        self.input_rect = None
        self.start_button_rect = None
        self.back_button_rect = None
        self.sound_toggle_rect = None
        self.language_toggle_rect = None
        
        # 鼠标悬停的等级
        self.hovered_level = None
        
        self._create_ui_elements()

    def _refresh_fonts(self):
        self.font = self.create_font(24)
        self.title_font = self.create_font(36)
        self.subtitle_font = self.create_font(28)
        self.small_font = self.create_font(20)

    def on_enter(self):
        """每次进入配置页时同步当前全局设置。"""
        self.current_level = self.manager.settings["start_level"]
        self.current_questions = self.manager.settings["total_questions"]
        self.current_sound_enabled = self.manager.settings.get("sound_enabled", True)
        self.current_language = self.manager.settings.get("language", "en-US")
        self.input_text = str(self.current_questions)

    def _create_ui_elements(self):
        """创建左右分栏布局：左侧配置，右侧预览"""
        # === 垂直分层布局 - 左右分栏设计 ===
        
        # 主标题区域
        self.title_y = 40
        
        # 操作说明区域
        self.info_y = 80
        
        # 难度等级区域 - 左侧
        self.level_title_y = 110  # 与操作说明保持30px间距
        card_width = 80
        card_height = 50
        cards_per_row = 4
        total_cards = 8
        
        # 左侧区域：难度等级配置
        left_section_center = 250  # 左侧区域中心点
        cards_total_width = cards_per_row * card_width + (cards_per_row - 1) * 15
        start_x = left_section_center - cards_total_width // 2
        self.level_cards_start_y = 140  # 与难度标题保持30px间距
        
        self.level_cards = []
        for i in range(total_cards):
            level = i + 1
            row = i // cards_per_row
            col = i % cards_per_row
            
            x = start_x + col * (card_width + 15)
            y = self.level_cards_start_y + row * (card_height + 15)
            
            rect = pygame.Rect(x, y, card_width, card_height)
            self.level_cards.append((rect, level))
        
        # 右侧区域：字号预览 - 完整尺寸，无任何限制
        right_section_center = 650  # 右侧区域中心点
        self.preview_title_y = 110  # 与左侧难度标题对齐
        self.preview_e_y = 200      # 预览E字位置，为最大字号预留充足垂直空间
        
        # 题目数量区域 - 居中显示
        self.question_title_y = 320  # 在预览区域下方适当位置
        self.input_rect = pygame.Rect(SCREEN_WIDTH // 2 - 60, 350, 120, 35)
        self.range_hint_y = 390
        
        # 状态摘要区域
        self.status_y = 430
        self.sound_toggle_rect = pygame.Rect(SCREEN_WIDTH // 2 - 100, 460, 200, 35)
        self.language_toggle_rect = pygame.Rect(SCREEN_WIDTH // 2 - 100, 500, 200, 35)

        # 操作按钮区域
        self.button_y = 550
        button_width = 120
        button_spacing = 20
        self.start_button_rect = pygame.Rect(SCREEN_WIDTH // 2 - button_width - button_spacing // 2, self.button_y, button_width, 40)
        self.back_button_rect = pygame.Rect(SCREEN_WIDTH // 2 + button_spacing // 2, self.button_y, button_width, 40)

    def _commit_settings(self):
        """将当前配置提交到全局并持久化。"""
        self.manager.settings["start_level"] = self.current_level
        self.manager.settings["total_questions"] = self.current_questions
        self.manager.settings["sound_enabled"] = self.current_sound_enabled
        self.manager.settings["language"] = self.current_language
        self.manager.apply_language_preference()
        self.manager.apply_sound_preference()
        self.manager.save_user_preferences()

    def _toggle_language(self):
        self.current_language = "zh-CN" if self.current_language == "en-US" else "en-US"

    def handle_events(self, events):
        mouse_pos = pygame.mouse.get_pos()
        
        # 更新鼠标悬停的等级
        self.hovered_level = None
        for rect, level in self.level_cards:
            if rect.collidepoint(mouse_pos):
                self.hovered_level = level
                break
        
        for event in events:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    # 返回菜单前保存设置
                    self._commit_settings()
                    self.manager.set_scene("menu")
                elif event.key == pygame.K_RETURN:
                    # 确认设置并开始训练
                    self._commit_settings()
                    self.manager.set_scene("training")
                elif event.key == pygame.K_m:
                    self.current_sound_enabled = not self.current_sound_enabled
                    self._commit_settings()
                elif event.key == pygame.K_l:
                    self._toggle_language()
                    self._commit_settings()
                elif event.key == pygame.K_UP:
                    # 向上选择上方的按钮（降低等级）
                    self.current_level = max(1, self.current_level - 1)
                elif event.key == pygame.K_DOWN:
                    # 向下选择下方的按钮（提高等级）
                    self.current_level = min(8, self.current_level + 1)
                
                # 处理输入框文本输入
                if self.input_active:
                    if event.key == pygame.K_BACKSPACE:
                        self.input_text = self.input_text[:-1]
                    elif event.key == pygame.K_RETURN:
                        self.input_active = False
                        self._validate_and_update_questions()
                    elif event.unicode.isdigit():
                        # 限制输入长度，避免过长（最多4位数字）
                        if len(self.input_text) < 4:
                            self.input_text += event.unicode
            
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:  # 左键点击
                    # 检查等级卡片点击
                    for rect, level in self.level_cards:
                        if rect.collidepoint(mouse_pos):
                            self.current_level = level
                    
                    # 检查输入框点击
                    if self.input_rect.collidepoint(mouse_pos):
                        self.input_active = True
                    else:
                        self.input_active = False
                        self._validate_and_update_questions()
                    
                    # 检查开始游戏按钮点击
                    if self.start_button_rect and self.start_button_rect.collidepoint(mouse_pos):
                        self._commit_settings()
                        self.manager.set_scene("training")
                    
                    # 检查返回按钮点击
                    if self.back_button_rect and self.back_button_rect.collidepoint(mouse_pos):
                        self._commit_settings()
                        self.manager.set_scene("menu")

                    # 检查音效开关点击
                    if self.sound_toggle_rect and self.sound_toggle_rect.collidepoint(mouse_pos):
                        self.current_sound_enabled = not self.current_sound_enabled
                        self._commit_settings()

                    # 检查语言开关点击
                    if self.language_toggle_rect and self.language_toggle_rect.collidepoint(mouse_pos):
                        self._toggle_language()
                        self._commit_settings()

    def _validate_and_update_questions(self):
        """验证输入并更新题目数量（支持0-1000范围）"""
        if self.input_text.strip() == "":
            self.input_text = "0"
        
        try:
            value = int(self.input_text)
            if value < MIN_QUESTIONS:
                value = MIN_QUESTIONS
            elif value > MAX_QUESTIONS:
                value = MAX_QUESTIONS
            self.current_questions = value
            self.input_text = str(value)
        except ValueError:
            # 如果输入无效，重置为默认值
            self.input_text = str(self.current_questions)

    def draw(self, screen):
        self._refresh_fonts()
        screen.fill((30, 30, 50))
        
        # === 主标题区域 ===
        title = self.title_font.render(self.manager.t("config.title"), True, (255, 255, 255))
        screen.blit(title, (SCREEN_WIDTH // 2 - title.get_width() // 2, self.title_y))
        
        # === 操作说明区域 ===
        info_text = self.small_font.render(self.manager.t("config.info"), True, (180, 180, 200))
        screen.blit(info_text, (SCREEN_WIDTH // 2 - info_text.get_width() // 2, self.info_y))
        
        # 获取鼠标位置用于悬停检测
        mouse_pos = pygame.mouse.get_pos()
        
        # === 左侧：难度等级配置区域 ===
        level_title = self.subtitle_font.render(self.manager.t("config.difficulty_level"), True, (255, 255, 255))
        screen.blit(level_title, (250 - level_title.get_width() // 2, self.level_title_y))
        
        # 绘制等级卡片（2行×4列网格）
        current_size = E_SIZE_LEVELS[self.current_level - 1]
        
        for rect, level in self.level_cards:
            size_value = E_SIZE_LEVELS[level - 1]
            is_selected = (level == self.current_level)
            is_hovered = rect.collidepoint(mouse_pos)
            
            # 卡片背景颜色
            if is_selected:
                card_color = (80, 120, 200)
                border_color = (150, 180, 255)
                text_color = (255, 255, 255)
            elif is_hovered:
                card_color = (70, 100, 180)
                border_color = (130, 160, 220)
                text_color = (255, 255, 255)
            else:
                card_color = (60, 60, 90)
                border_color = (100, 100, 150)
                text_color = (200, 200, 220)
            
            # 绘制卡片背景
            pygame.draw.rect(screen, card_color, rect, border_radius=6)
            pygame.draw.rect(screen, border_color, rect, 2, border_radius=6)
            
            # 绘制等级文本 (L1, L2, ...)
            level_text = self.font.render(f"L{level}", True, text_color)
            screen.blit(level_text, (rect.centerx - level_text.get_width() // 2, 
                                   rect.y + 6))
            
            # 绘制尺寸文本 (10px, 20px, ...)
            size_text = self.small_font.render(f"{size_value}px", True, text_color)
            screen.blit(size_text, (rect.centerx - size_text.get_width() // 2, 
                                  rect.y + 28))
        
        # === 右侧：字号预览区域 - 完整尺寸，无任何限制 ===
        preview_title = self.subtitle_font.render(self.manager.t("config.font_preview"), True, (255, 255, 255))
        screen.blit(preview_title, (650 - preview_title.get_width() // 2, self.preview_title_y))
        
        # 确定要预览的字号：优先显示悬停的等级，否则显示当前选中等级
        preview_level = self.hovered_level if self.hovered_level is not None else self.current_level
        preview_size = E_SIZE_LEVELS[preview_level - 1]
        
        # 绘制E字预览 - 完整尺寸，无任何限制！
        # 位置经过精确计算，确保即使最大字号80px也不会超出屏幕边界
        self.e_generator.draw_e(screen, (650, self.preview_e_y), preview_size, "RIGHT")
        
        # === 题目数量区域 - 居中显示 ===
        question_title = self.subtitle_font.render(self.manager.t("config.question_count"), True, (255, 255, 255))
        screen.blit(question_title, (SCREEN_WIDTH // 2 - question_title.get_width() // 2, self.question_title_y))
        
        # 输入框
        input_hovered = self.input_rect.collidepoint(mouse_pos)
        input_color = (200, 220, 240) if self.input_active else (180, 200, 220) if input_hovered else (150, 170, 190)
        border_color = (100, 150, 200) if self.input_active else (80, 120, 160)
        
        pygame.draw.rect(screen, input_color, self.input_rect, border_radius=6)
        pygame.draw.rect(screen, border_color, self.input_rect, 2, border_radius=6)
        
        # 输入框文字（精确垂直居中）
        input_text_surface = self.font.render(self.input_text, True, (0, 0, 0))
        text_height = input_text_surface.get_height()
        text_y = self.input_rect.y + (self.input_rect.height - text_height) // 2
        screen.blit(input_text_surface, (self.input_rect.x + 10, text_y))
        
        # 输入范围提示
        range_hint = self.small_font.render(
            self.manager.t("config.range", min_questions=MIN_QUESTIONS, max_questions=MAX_QUESTIONS),
            True,
            (180, 180, 200)
        )
        screen.blit(range_hint, (SCREEN_WIDTH // 2 - range_hint.get_width() // 2, self.range_hint_y))
        
        # === 状态摘要区域 ===
        status_text = self.manager.t(
            "config.status",
            level=self.current_level,
            size=current_size,
            questions=self.current_questions
        )
        status_surface = self.small_font.render(status_text, True, (180, 220, 180))
        screen.blit(status_surface, (SCREEN_WIDTH // 2 - status_surface.get_width() // 2, self.status_y))

        # 音效开关
        toggle_hovered = self.sound_toggle_rect.collidepoint(mouse_pos)
        toggle_bg = (90, 150, 90) if self.current_sound_enabled else (150, 90, 90)
        if toggle_hovered:
            toggle_bg = (min(toggle_bg[0] + 20, 255), min(toggle_bg[1] + 20, 255), min(toggle_bg[2] + 20, 255))

        pygame.draw.rect(screen, toggle_bg, self.sound_toggle_rect, border_radius=8)
        pygame.draw.rect(screen, (220, 220, 220), self.sound_toggle_rect, 2, border_radius=8)

        sound_label = self.manager.t("config.sound_on") if self.current_sound_enabled else self.manager.t("config.sound_off")
        sound_text = self.font.render(sound_label, True, (255, 255, 255))
        screen.blit(sound_text, (self.sound_toggle_rect.centerx - sound_text.get_width() // 2,
                               self.sound_toggle_rect.centery - sound_text.get_height() // 2))

        # 语言开关
        lang_hovered = self.language_toggle_rect.collidepoint(mouse_pos)
        lang_bg = (90, 120, 170)
        if lang_hovered:
            lang_bg = (110, 140, 190)

        pygame.draw.rect(screen, lang_bg, self.language_toggle_rect, border_radius=8)
        pygame.draw.rect(screen, (220, 220, 220), self.language_toggle_rect, 2, border_radius=8)

        current_lang_name = self.manager.t("config.lang_en") if self.current_language == "en-US" else self.manager.t("config.lang_zh")
        lang_label = self.manager.t("config.language", language=current_lang_name)
        lang_text = self.font.render(lang_label, True, (255, 255, 255))
        screen.blit(lang_text, (self.language_toggle_rect.centerx - lang_text.get_width() // 2,
                              self.language_toggle_rect.centery - lang_text.get_height() // 2))
        
        # === 操作按钮区域 ===
        # 开始游戏按钮
        start_button_hovered = self.start_button_rect.collidepoint(mouse_pos)
        start_button_color = (80, 200, 100) if start_button_hovered else (60, 160, 80)
        start_border_color = (150, 240, 180) if start_button_hovered else (120, 200, 140)
        
        pygame.draw.rect(screen, start_button_color, self.start_button_rect, border_radius=8)
        pygame.draw.rect(screen, start_border_color, self.start_button_rect, 2, border_radius=8)
        
        start_text = self.font.render(self.manager.t("config.start_game"), True, (255, 255, 255))
        screen.blit(start_text, (self.start_button_rect.centerx - start_text.get_width() // 2,
                               self.start_button_rect.centery - start_text.get_height() // 2))
        
        # 返回按钮
        back_button_hovered = self.back_button_rect.collidepoint(mouse_pos)
        back_button_color = (120, 120, 160) if back_button_hovered else (90, 90, 130)
        back_border_color = (180, 180, 220) if back_button_hovered else (150, 150, 190)
        
        pygame.draw.rect(screen, back_button_color, self.back_button_rect, border_radius=8)
        pygame.draw.rect(screen, back_border_color, self.back_button_rect, 2, border_radius=8)
        
        back_text = self.font.render(self.manager.t("config.back"), True, (255, 255, 255))
        screen.blit(back_text, (self.back_button_rect.centerx - back_text.get_width() // 2,
                              self.back_button_rect.centery - back_text.get_height() // 2))
