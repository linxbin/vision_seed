import pygame
import sys
import os
import unittest
from unittest.mock import patch

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tests.ui_test_base import UITestCase
from games.accommodation.e_orientation.scenes.history_scene import HistoryScene


class TestHistorySceneUI(UITestCase):
    """历史记录场景UI测试"""
    
    def setUp(self):
        super().setUp()
        # 创建模拟的场景管理器
        self.mock_manager = self.create_mock_scene_manager()
        # 模拟历史记录数据
        self.mock_manager.data_manager.get_all_sessions.return_value = [
            {
                "timestamp": "2026-03-02T13:00:00",
                "difficulty_level": 3,
                "e_size_px": 30,
                "total_questions": 30,
                "correct_count": 25,
                "wrong_count": 5,
                "duration_seconds": 120.5,
                "accuracy_rate": 83.3
            },
            {
                "timestamp": "2026-03-02T12:00:00", 
                "difficulty_level": 2,
                "e_size_px": 20,
                "total_questions": 20,
                "correct_count": 18,
                "wrong_count": 2,
                "duration_seconds": 80.0,
                "accuracy_rate": 90.0
            }
        ]
        # 创建历史记录场景实例
        self.scene = HistoryScene(self.mock_manager)
        # 调用on_enter以加载数据
        self.scene.on_enter()
    
    def test_scene_initialization(self):
        """测试历史记录场景初始化状态"""
        self.assertIsNotNone(self.scene.manager)
        self.assertEqual(len(self.scene.raw_records), 2)  # 2条测试记录
        self.assertEqual(len(self.scene.filtered_records), 2)  # 默认显示所有记录
        
        # 验证过滤控件创建正确
        self.assertIsNotNone(self.scene.date_all_rect)
        self.assertIsNotNone(self.scene.level_value_rect)
        self.assertIsNotNone(self.scene.sort_time_rect)
    
    def test_history_rendering_basic(self):
        """测试历史记录的基本渲染"""
        frame = self.capture_frame(self.scene)
        
        # 获取屏幕中心区域的平均颜色（应该有历史记录内容渲染）
        center_x = frame.get_width() // 2
        center_y = frame.get_height() // 2
        
        center_color = self.get_surface_average_color(
            frame, 
            (center_x - 150, center_y - 150, 300, 300)
        )
        
        # 历史记录应该有内容渲染（不是纯黑屏）
        self.assertGreater(
            sum(center_color[:3]), 
            10,
            f"历史记录场景未正确渲染，实际RGB总和: {sum(center_color[:3])}"
        )
    
    def test_filter_controls_interaction(self):
        """测试过滤控件交互"""
        # 设置鼠标位置在"7天"过滤按钮上
        date_7d_pos = (
            self.scene.date_7d_rect.centerx,
            self.scene.date_7d_rect.centery
        )
        self.set_mouse_position(*date_7d_pos)
        
        # 模拟点击7天过滤按钮
        click_events = self.simulate_mouse_event(
            pygame.MOUSEBUTTONDOWN,
            date_7d_pos,
            button=1
        )
        
        # 捕获点击后的帧
        result_frame = self.capture_frame(self.scene, click_events)
        
        # 验证过滤状态已更新
        self.assertEqual(self.scene.date_filter, "7d")
    
    def test_back_button_navigation(self):
        """测试返回按钮导航"""
        # 设置鼠标位置在返回按钮上
        back_pos = (
            self.scene.back_button_rect.centerx,
            self.scene.back_button_rect.centery
        )
        self.set_mouse_position(*back_pos)
        
        # 模拟点击返回按钮
        click_events = self.simulate_mouse_event(
            pygame.MOUSEBUTTONDOWN,
            back_pos,
            button=1
        )
        
        # 捕获点击后的帧
        result_frame = self.capture_frame(self.scene, click_events)
        
        # 验证场景切换逻辑被触发
        self.mock_manager.set_scene.assert_called_with("menu")


if __name__ == '__main__':
    unittest.main()
