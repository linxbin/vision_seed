import pygame
from datetime import datetime
from core.base_scene import BaseScene
from config import SCREEN_WIDTH, SCREEN_HEIGHT


class HistoryScene(BaseScene):
    """历史记录场景 - 显示所有训练记录"""

    def __init__(self, manager):
        super().__init__(manager)
        self._refresh_fonts()
        
        # 返回按钮（右上角，像素级精确位置）
        self.back_button_rect = pygame.Rect(SCREEN_WIDTH - 80, 20, 60, 30)
        
        # 分页相关变量
        self.records_per_page = 8
        self.current_page = 0
        self.total_pages = 0
        
        # 不在初始化时加载数据，改为每次进入场景时加载
        self.all_records = []
        self.total_pages = 1

    def _refresh_fonts(self):
        self.title_font = self.create_font(48)
        self.header_font = self.create_font(32)
        self.record_font = self.create_font(26)
        self.small_font = self.create_font(24)

    def on_enter(self):
        """进入场景时加载一次最新数据，避免每帧读文件。"""
        self._load_records()

    def _load_records(self):
        """加载所有训练记录"""
        try:
            self.all_records = self.manager.data_manager.get_all_sessions()
            self.total_pages = max(1, (len(self.all_records) + self.records_per_page - 1) // self.records_per_page)
            self.current_page = min(self.current_page, self.total_pages - 1)
        except Exception as e:
            print(f"Error loading records: {e}")
            self.all_records = []
            self.total_pages = 1

    def _format_timestamp(self, timestamp_str):
        """格式化时间戳为可读格式"""
        try:
            dt = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
            return dt.strftime("%Y-%m-%d %H:%M")
        except (ValueError, AttributeError):
            return self.manager.t("history.invalid_date")

    def _get_current_page_records(self):
        """获取当前页面的记录"""
        start_idx = self.current_page * self.records_per_page
        end_idx = start_idx + self.records_per_page
        return self.all_records[start_idx:end_idx]

    def handle_events(self, events):
        mouse_pos = pygame.mouse.get_pos()
        
        for event in events:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.manager.set_scene("menu")
                elif event.key == pygame.K_LEFT:
                    # 上一页
                    self.current_page = max(0, self.current_page - 1)
                elif event.key == pygame.K_RIGHT:
                    # 下一页
                    self.current_page = min(self.total_pages - 1, self.current_page + 1)
                elif event.key == pygame.K_r:
                    # 手动刷新
                    self._load_records()
            
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:  # 左键点击
                    if self.back_button_rect.collidepoint(mouse_pos):
                        self.manager.set_scene("menu")

    def update(self):
        """历史页不需要逐帧更新逻辑。"""
        pass

    def draw(self, screen):
        self._refresh_fonts()
        screen.fill((25, 25, 45))
        
        # 获取鼠标位置用于悬停检测
        mouse_pos = pygame.mouse.get_pos()
        
        # 绘制标题
        title = self.title_font.render(self.manager.t("history.title"), True, (255, 255, 255))
        screen.blit(title, (SCREEN_WIDTH // 2 - title.get_width() // 2, 40))
        
        # 绘制操作说明
        if self.all_records:
            info_text = self.small_font.render(self.manager.t("history.info_with_records"), True, (180, 180, 200))
        else:
            info_text = self.small_font.render(self.manager.t("history.info_empty"), True, (200, 150, 150))
        screen.blit(info_text, (SCREEN_WIDTH // 2 - info_text.get_width() // 2, 85))
        
        if not self.all_records:
            # 如果没有记录，显示提示信息并返回按钮
            self._draw_back_button(screen, mouse_pos)
            return
        
        # 计算当前页面记录
        current_records = self._get_current_page_records()
        
        # 表头 - 列内容居中
        header_y = 120
        headers = [
            self.manager.t("history.header.datetime"),
            self.manager.t("history.header.level"),
            self.manager.t("history.header.questions"),
            self.manager.t("history.header.correct"),
            self.manager.t("history.header.accuracy"),
            self.manager.t("history.header.duration"),
        ]

        table_left = 60
        col_widths = [240, 90, 110, 100, 110, 130]
        col_centers = []
        cursor = table_left
        for width in col_widths:
            col_centers.append(cursor + width // 2)
            cursor += width
        
        for i, header in enumerate(headers):
            header_surface = self.header_font.render(header, True, (200, 220, 255))
            header_x = col_centers[i] - header_surface.get_width() // 2
            screen.blit(header_surface, (header_x, header_y))
        
        # 绘制分隔线
        pygame.draw.line(screen, (80, 100, 140), (60, header_y + 35), (SCREEN_WIDTH - 60, header_y + 35), 2)
        
        # 绘制记录
        record_start_y = header_y + 50
        record_height = 40
        
        for i, record in enumerate(current_records):
            y_pos = record_start_y + i * record_height
            
            # 背景色交替（提高可读性）
            if i % 2 == 0:
                bg_color = (35, 35, 55)
                text_color = (220, 220, 240)
            else:
                bg_color = (40, 40, 60)
                text_color = (200, 200, 220)
            
            # 绘制背景（可选，根据美观度调整）
            record_rect = pygame.Rect(60, y_pos, SCREEN_WIDTH - 120, record_height - 5)
            pygame.draw.rect(screen, bg_color, record_rect, border_radius=4)
            
            # 格式化数据显示
            timestamp = self._format_timestamp(record.get("timestamp", ""))
            level = str(record.get("difficulty_level", "N/A"))
            questions = str(record.get("total_questions", "N/A"))
            correct = str(record.get("correct_count", "N/A"))
            accuracy = f"{record.get('accuracy_rate', 0.0):.1f}%"
            duration = f"{record.get('duration_seconds', 0):.2f}s"
            
            record_data = [timestamp, level, questions, correct, accuracy, duration]
            
            for j, data in enumerate(record_data):
                data_surface = self.record_font.render(data, True, text_color)
                # 精确垂直居中：计算文字高度并调整Y坐标
                text_height = data_surface.get_height()
                text_y = y_pos + (record_height - 5 - text_height) // 2
                text_x = col_centers[j] - data_surface.get_width() // 2
                screen.blit(data_surface, (text_x, text_y))
        
        # 绘制分页信息
        if self.total_pages > 1:
            page_info = self.manager.t("history.page_info", current=self.current_page + 1, total=self.total_pages)
            page_surface = self.small_font.render(page_info, True, (180, 200, 220))
            screen.blit(page_surface, (SCREEN_WIDTH // 2 - page_surface.get_width() // 2, 
                                  record_start_y + len(current_records) * record_height + 20))
        
        # 绘制返回按钮
        self._draw_back_button(screen, mouse_pos)

    def _draw_back_button(self, screen, mouse_pos):
        """绘制返回按钮（右上角，强迫症级别的精确位置）"""
        is_hovered = self.back_button_rect.collidepoint(mouse_pos)
        
        # 按钮背景色
        button_color = (80, 120, 200) if is_hovered else (60, 90, 150)
        border_color = (150, 180, 255) if is_hovered else (100, 130, 200)
        
        pygame.draw.rect(screen, button_color, self.back_button_rect, border_radius=6)
        pygame.draw.rect(screen, border_color, self.back_button_rect, 2, border_radius=6)
        
        # 按钮文字
        back_text = self.small_font.render(self.manager.t("history.back"), True, (255, 255, 255))
        text_x = self.back_button_rect.centerx - back_text.get_width() // 2
        text_y = self.back_button_rect.centery - back_text.get_height() // 2
        screen.blit(back_text, (text_x, text_y))
