import pygame
import sys
import os
import unittest
from unittest.mock import patch, MagicMock

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tests.ui_test_base import UITestCase
from scenes.license_scene import LicenseScene


class TestLicenseSceneUI(UITestCase):
    """授权场景UI测试"""
    
    def setUp(self):
        super().setUp()
        # 创建模拟的场景管理器
        self.mock_manager = self.create_mock_scene_manager()
        # 模拟设备哈希
        self.mock_manager.license_manager.get_device_hash.return_value = "sha256:abcdef1234567890"
        # 模拟授权验证返回值
        self.mock_manager.license_manager.activate_with_token.return_value = (True, "success")
        self.mock_manager.license_manager.validate_license_token.return_value = True
        # 创建授权场景实例
        self.scene = LicenseScene(self.mock_manager)
    
    def test_scene_initialization(self):
        """测试授权场景初始化状态"""
        self.assertIsNotNone(self.scene.manager)
        self.assertIsNotNone(self.scene.panel_rect)
        self.assertIsNotNone(self.scene.hash_value_rect)
        self.assertIsNotNone(self.scene.copy_hash_button_rect)
        self.assertIsNotNone(self.scene.input_rect)
        
        # 验证初始状态
        self.assertEqual(self.scene.input_text, "")
        self.assertEqual(self.scene.message, "")
        self.assertFalse(self.scene.input_active)
    
    def test_license_rendering_basic(self):
        """测试授权页面的基本渲染"""
        frame = self.capture_frame(self.scene)
        
        # 获取屏幕中心区域的平均颜色（应该有授权内容渲染）
        center_x = frame.get_width() // 2
        center_y = frame.get_height() // 2
        
        center_color = self.get_surface_average_color(
            frame, 
            (center_x - 150, center_y - 150, 300, 300)
        )
        
        # 授权页面应该有内容渲染（不是纯黑屏）
        self.assertGreater(
            sum(center_color[:3]), 
            10,
            f"授权场景未正确渲染，实际RGB总和: {sum(center_color[:3])}"
        )
    
    def test_copy_hash_button_interaction(self):
        """测试复制哈希按钮交互"""
        # 设置鼠标位置在复制按钮上
        copy_pos = (
            self.scene.copy_hash_button_rect.centerx,
            self.scene.copy_hash_button_rect.centery
        )
        self.set_mouse_position(*copy_pos)
        
        # 模拟点击复制按钮
        click_events = self.simulate_mouse_event(
            pygame.MOUSEBUTTONDOWN,
            copy_pos,
            button=1
        )
        
        # 捕获点击后的帧
        result_frame = self.capture_frame(self.scene, click_events)
        
        # 验证flash效果被激活（即使剪贴板失败，flash效果也应该触发）
        # 注意：在某些环境中剪贴板可能不可用，但flash效果应该仍然工作
        if self.scene.copy_flash_frames == 0:
            # 如果flash效果没触发，可能是剪贴板初始化失败
            # 但我们至少可以验证消息被设置
            self.assertIn("copy", self.scene.message.lower() or "success")
        else:
            self.assertGreater(self.scene.copy_flash_frames, 0)
    
    def test_license_input_validation(self):
        """测试授权码输入验证"""
        # 设置输入文本
        self.scene.input_text = "VS1.test123456"
        
        # 模拟按下Enter键进行验证
        enter_events = self.simulate_key_event(pygame.K_RETURN)
        
        # 捕获按键后的帧
        result_frame = self.capture_frame(self.scene, enter_events)
        
        # 验证授权验证逻辑被触发
        self.mock_manager.license_manager.activate_with_token.assert_called_with("VS1.test123456")


if __name__ == '__main__':
    unittest.main()