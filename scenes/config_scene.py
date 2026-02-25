import pygame
from core.base_scene import BaseScene
from core.e_generator import EGenerator
from config import E_SIZE_LEVELS, SCREEN_WIDTH, SCREEN_HEIGHT, MIN_QUESTIONS, MAX_QUESTIONS


class ConfigScene(BaseScene):
    """配置场景 - 用于设置难度等级和题目数量"""

    def __init__(self, manager):
        super().__init__(manager)
        self.font = pygame.font.SysFont(None, 28)
        self.title_font = pygame.font.SysFont(None, 42)
        self.small_font = pygame.font.SysFont(None, 24)
        self.e_generator = EGenerator()
        
        # 初始化当前选中的设置（从settings中读取）
        self.current_level = self.manager.settings["start_level"]
        self.current_questions = self.manager.settings["total_questions"]
        
        # 确保当前题目数量在有效范围内
        if self.current_questions < MIN_QUESTIONS:
            self.current_questions = MIN_QUESTIONS
        elif self.current_questions > MAX_QUESTIONS:
            self.current_questions = MAX_QUESTIONS
        
        # 输入框相关变量
        self.input_active = False
        self.input_text = str(self.current_questions)
        self.input_rect = None
        
        # 定义UI元素的矩形区域
        self.level_buttons = []
        self.start_button_rect = None
        self.back_button_rect = None
        
        self._create_ui_elements()

    def _create_ui_elements(self):
        """创建所有UI元素的矩形区域"""
        # 难度等级按钮
        button_start_y = 120
        button_height = 35
        button_width = 160
        
        self.level_buttons = []
        for i in range(8):
            level = i + 1
            y_pos = button_start_y + i * (button_height + 6)
            rect = pygame.Rect(60, y_pos, button_width, button_height)
            self.level_buttons.append((rect, level))
        
        # 题目数量输入框 - 精确对齐到右半部分中心
        input_x = SCREEN_WIDTH - 200  # 右半部分中心点
        self.input_rect = pygame.Rect(input_x - 60, 160, 120, 35)
        
        # 开始游戏按钮
        self.start_button_rect = pygame.Rect(SCREEN_WIDTH // 2 - 80, SCREEN_HEIGHT - 80, 160, 45)
        
        # 返回按钮（右上角）
        self.back_button_rect = pygame.Rect(SCREEN_WIDTH - 80, 20, 60, 30)

    def handle_events(self, events):
        mouse_pos = pygame.mouse.get_pos()
        
        for event in events:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    # 返回菜单前保存设置
                    self.manager.settings["start_level"] = self.current_level
                    self.manager.settings["total_questions"] = self.current_questions
                    self.manager.set_scene("menu")
                elif event.key == pygame.K_RETURN:
                    # 确认设置并开始训练
                    self.manager.settings["start_level"] = self.current_level
                    self.manager.settings["total_questions"] = self.current_questions
                    self.manager.set_scene("training")
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
                        # 限制输入长度，避免过长
                        if len(self.input_text) < 4:
                            self.input_text += event.unicode
            
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:  # 左键点击
                    # 检查难度等级按钮点击
                    for rect, level in self.level_buttons:
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
                        self.manager.settings["start_level"] = self.current_level
                        self.manager.settings["total_questions"] = self.current_questions
                        self.manager.set_scene("training")
                    
                    # 检查返回按钮点击
                    if self.back_button_rect and self.back_button_rect.collidepoint(mouse_pos):
                        self.manager.settings["start_level"] = self.current_level
                        self.manager.settings["total_questions"] = self.current_questions
                        self.manager.set_scene("menu")

    def _validate_and_update_questions(self):
        """验证输入并更新题目数量"""
        if self.input_text.strip() == "":
            self.input_text = "50"
        
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
        screen.fill((30, 30, 50))
        
        # 绘制标题
        title = self.title_font.render("Game Configuration", True, (255, 255, 255))
        screen.blit(title, (SCREEN_WIDTH // 2 - title.get_width() // 2, 40))
        
        # 绘制操作说明
        info_text = self.small_font.render("↑↓: 难度等级  鼠标: 选择选项  Enter/ESC: 开始/返回", True, (180, 180, 200))
        screen.blit(info_text, (SCREEN_WIDTH // 2 - info_text.get_width() // 2, 85))
        
        # 获取鼠标位置用于悬停检测
        mouse_pos = pygame.mouse.get_pos()
        
        # 左侧：难度等级配置
        level_title = self.font.render("Difficulty Level:", True, (255, 255, 255))
        screen.blit(level_title, (60, 95))
        
        for rect, level in self.level_buttons:
            # 检查鼠标悬停或选中状态
            is_hovered = rect.collidepoint(mouse_pos)
            is_selected = (level == self.current_level)
            
            # 按钮背景颜色
            if is_selected:
                button_color = (80, 120, 200)
                border_color = (150, 180, 255)
            elif is_hovered:
                button_color = (70, 100, 180)
                border_color = (130, 160, 220)
            else:
                button_color = (60, 60, 90)
                border_color = (100, 100, 150)
            
            pygame.draw.rect(screen, button_color, rect)
            pygame.draw.rect(screen, border_color, rect, 2)
            
            # 按钮文字
            level_text = f"Level {level}"
            size_text = f"({E_SIZE_LEVELS[level-1]}px)"
            full_text = f"{level_text} {size_text}"
            text_surface = self.small_font.render(full_text, True, (255, 255, 255))
            screen.blit(text_surface, (rect.centerx - text_surface.get_width() // 2,
                                     rect.centery - text_surface.get_height() // 2))
        
        # 中部：E字预览（与难度等级保持严格的垂直对齐）
        e_preview_x = 280  # 与难度等级区域保持120px水平间距
        e_preview_y = 180  # 与难度等级标题保持严格的垂直对齐基准
        current_size = E_SIZE_LEVELS[self.current_level - 1]
        
        # 计算预览框大小，确保有足够的内边距（20px）
        preview_padding = 20
        preview_size = min(current_size + preview_padding * 2, 200)
        
        # 绘制预览框
        pygame.draw.rect(screen, (50, 50, 80), 
                        (e_preview_x - preview_size//2, 
                         e_preview_y - preview_size//2, 
                         preview_size, preview_size))
        pygame.draw.rect(screen, (100, 100, 150), 
                        (e_preview_x - preview_size//2, 
                         e_preview_y - preview_size//2, 
                         preview_size, preview_size), 2)
        
        # 绘制E字预览
        preview_e_size = min(current_size, 160)
        self.e_generator.draw_e(screen, (e_preview_x, e_preview_y), preview_e_size, "RIGHT")
        
        # E字预览标题（严格对齐到预览框上方30px）
        preview_title = self.small_font.render("E Preview", True, (255, 255, 255))
        screen.blit(preview_title, (e_preview_x - preview_title.get_width() // 2, 
                                  e_preview_y - preview_size//2 - 30))
        
        # 右半部分：题目数量配置（完美对齐和间距控制）
        right_section_center = SCREEN_WIDTH - 200  # 右半部分视觉中心
        
        # 题目数量标题（与E字预览标题保持相同的垂直基准线）
        question_title = self.font.render("Question Count:", True, (255, 255, 255))
        question_title_y = e_preview_y - preview_size//2 - 30  # 与E预览标题完全对齐
        screen.blit(question_title, (right_section_center - question_title.get_width() // 2, question_title_y))
        
        # 输入框（精确居中对齐到右半部分中心）
        input_hovered = self.input_rect.collidepoint(mouse_pos)
        input_color = (200, 220, 240) if self.input_active else (180, 200, 220) if input_hovered else (150, 170, 190)
        border_color = (100, 150, 200) if self.input_active else (80, 120, 160)
        
        pygame.draw.rect(screen, input_color, self.input_rect)
        pygame.draw.rect(screen, border_color, self.input_rect, 2)
        
        # 输入框文字（精确内边距：左10px，上5px）
        input_text_surface = self.font.render(self.input_text, True, (0, 0, 0))
        screen.blit(input_text_surface, (self.input_rect.x + 10, self.input_rect.y + 5))
        
        # 输入范围提示（与输入框保持25px垂直间距）
        range_hint = self.small_font.render(f"Range: {MIN_QUESTIONS}-{MAX_QUESTIONS}", True, (180, 180, 200))
        range_hint_y = self.input_rect.bottom + 25  # 严格25px间距
        screen.blit(range_hint, (right_section_center - range_hint.get_width() // 2, range_hint_y))
        
        # 底部：开始游戏按钮
        start_button_hovered = self.start_button_rect.collidepoint(mouse_pos)
        start_button_color = (80, 200, 100) if start_button_hovered else (60, 160, 80)
        start_border_color = (150, 240, 180) if start_button_hovered else (120, 200, 140)
        
        pygame.draw.rect(screen, start_button_color, self.start_button_rect)
        pygame.draw.rect(screen, start_border_color, self.start_button_rect, 3)
        
        start_text = self.font.render("Start Game", True, (255, 255, 255))
        screen.blit(start_text, (self.start_button_rect.centerx - start_text.get_width() // 2,
                               self.start_button_rect.centery - start_text.get_height() // 2))
        
        # 状态信息（放在开始游戏按钮上方，保持严格的25px间距）
        status_text = f"Selected: Level {self.current_level} ({current_size}px), Questions: {self.current_questions}"
        status_surface = self.small_font.render(status_text, True, (180, 220, 180))
        status_y = self.start_button_rect.top - 25  # 严格25px间距
        screen.blit(status_surface, (SCREEN_WIDTH // 2 - status_surface.get_width() // 2, status_y))
        
        # 返回按钮（右上角，像素级精确位置）
        back_button_hovered = self.back_button_rect.collidepoint(mouse_pos)
        back_button_color = (80, 120, 200) if back_button_hovered else (60, 90, 150)
        back_border_color = (150, 180, 255) if back_button_hovered else (100, 130, 200)
        
        pygame.draw.rect(screen, back_button_color, self.back_button_rect, border_radius=6)
        pygame.draw.rect(screen, back_border_color, self.back_button_rect, 2, border_radius=6)
        
        back_text = self.small_font.render("Back", True, (255, 255, 255))
        back_text_x = self.back_button_rect.centerx - back_text.get_width() // 2
        back_text_y = self.back_button_rect.centery - back_text.get_height() // 2
        screen.blit(back_text, (back_text_x, back_text_y))