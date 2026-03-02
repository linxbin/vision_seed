import pygame
import sys
import os
import unittest
from unittest.mock import patch

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tests.ui_test_base import UITestCase
from scenes.menu_scene import MenuScene


class TestMenuSceneUI(UITestCase):
    """菜单场景UI测试"""
    
    def setUp(self):
        super().setUp()
        # 创建模拟的场景管理器
        self.mock_manager = self.create_mock_scene_manager()
        # 创建菜单场景实例
        self.scene = MenuScene(self.mock_manager)
    
    def test_scene_initialization(self):
        """测试菜单场景初始化状态"""
        self.assertIsNotNone(self.scene.manager)
        self.assertEqual(len(self.scene.menu_options), 4)  # 4个主菜单选项
        self.assertEqual(len(self.scene.templates), 3)    # 3个模板选项
        
        # 验证菜单选项配置正确
        first_option = self.scene.menu_options[0]
        self.assertEqual(first_option["key"], "menu.start_training")
        self.assertEqual(first_option["scene"], "training")
    
    def test_menu_rendering_basic(self):
        """测试菜单的基本渲染"""
        frame = self.capture_frame(self.scene)
        
        # 获取屏幕中心区域的平均颜色（应该有菜单渲染）
        center_x = frame.get_width() // 2
        center_y = frame.get_height() // 2
        
        center_color = self.get_surface_average_color(
            frame, 
            (center_x - 100, center_y - 100, 200, 200)
        )
        
        # 菜单应该有内容渲染（不是纯黑屏）
        self.assertGreater(
            sum(center_color[:3]), 
            10,
            f"菜单场景未正确渲染，实际RGB总和: {sum(center_color[:3])}"
        )
    
    def test_mouse_hover_interaction(self):
        """测试鼠标悬停交互"""
        # 获取第一个菜单选项的位置
        first_menu_rect = self.scene.menu_options[0]["rect"]
        hover_pos = (first_menu_rect.centerx, first_menu_rect.centery)
        
        # 设置鼠标位置用于悬停检测
        self.set_mouse_position(*hover_pos)
        
        # 捕获悬停状态的帧
        hover_frame = self.capture_frame(self.scene)
        
        # 捕获非悬停状态的帧（鼠标在其他位置）
        self.set_mouse_position(0, 0)  # 远离菜单的位置
        initial_frame = self.capture_frame(self.scene)
        
        # 验证UI有变化（悬停状态应该有视觉反馈）
        initial_sum = sum(self.get_surface_average_color(initial_frame)[:3])
        hover_sum = sum(self.get_surface_average_color(hover_frame)[:3])
        
        self.assertNotEqual(
            initial_sum,
            hover_sum,
            "鼠标悬停菜单选项应该有视觉反馈"
        )
    
    def test_menu_click_navigation(self):
        """测试菜单点击导航"""
        # 获取配置菜单选项的位置
        config_option = None
        for option in self.scene.menu_options:
            if option["scene"] == "config":
                config_option = option
                break
        
        self.assertIsNotNone(config_option, "未找到配置菜单选项")
        
        # 设置鼠标位置在配置菜单上
        click_pos = (config_option["rect"].centerx, config_option["rect"].centery)
        self.set_mouse_position(*click_pos)
        
        # 模拟点击配置菜单
        click_events = self.simulate_mouse_event(
            pygame.MOUSEBUTTONDOWN,
            click_pos,
            button=1
        )
        
        # 捕获点击后的帧
        result_frame = self.capture_frame(self.scene, click_events)
        
        # 验证场景切换逻辑被触发
        self.mock_manager.set_scene.assert_called_with("config")


if __name__ == '__main__':
    unittest.main()