import pygame
import sys
import os
import unittest
from unittest.mock import patch

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tests.ui_test_base import UITestCase
from scenes.onboarding_scene import OnboardingScene


class TestOnboardingSceneUI(UITestCase):
    """首次引导场景UI测试"""
    
    def setUp(self):
        super().setUp()
        # 创建模拟的场景管理器
        self.mock_manager = self.create_mock_scene_manager()
        # 创建首次引导场景实例
        self.scene = OnboardingScene(self.mock_manager)
    
    def test_scene_initialization(self):
        """测试首次引导场景初始化状态"""
        self.assertIsNotNone(self.scene.manager)
        self.assertIsNotNone(self.scene.panel_rect)
        self.assertIsNotNone(self.scene.start_button_rect)
        self.assertIsNotNone(self.scene.skip_button_rect)
        
        # 验证面板位置居中
        self.assertEqual(
            self.scene.panel_rect.centerx,
            self.test_surface.get_width() // 2
        )
    
    def test_onboarding_rendering_basic(self):
        """测试首次引导的基本渲染"""
        frame = self.capture_frame(self.scene)
        
        # 获取屏幕中心区域的平均颜色（应该有引导内容渲染）
        center_x = frame.get_width() // 2
        center_y = frame.get_height() // 2
        
        center_color = self.get_surface_average_color(
            frame, 
            (center_x - 150, center_y - 150, 300, 300)
        )
        
        # 引导页面应该有内容渲染（不是纯黑屏）
        self.assertGreater(
            sum(center_color[:3]), 
            10,
            f"首次引导场景未正确渲染，实际RGB总和: {sum(center_color[:3])}"
        )
    
    def test_start_button_interaction(self):
        """测试开始按钮交互"""
        # 设置鼠标位置在开始按钮上
        start_pos = (
            self.scene.start_button_rect.centerx,
            self.scene.start_button_rect.centery
        )
        self.set_mouse_position(*start_pos)
        
        # 模拟点击开始按钮
        click_events = self.simulate_mouse_event(
            pygame.MOUSEBUTTONDOWN,
            start_pos,
            button=1
        )
        
        # 捕获点击后的帧
        result_frame = self.capture_frame(self.scene, click_events)
        
        # 验证场景切换逻辑被触发
        self.mock_manager.set_scene.assert_called_with("menu")
        # 验证用户偏好已保存
        self.mock_manager.save_user_preferences.assert_called()
    
    def test_keyboard_navigation(self):
        """测试键盘导航"""
        # 模拟按下Enter键
        enter_events = self.simulate_key_event(pygame.K_RETURN)
        
        # 捕获按键后的帧
        result_frame = self.capture_frame(self.scene, enter_events)
        
        # 验证场景切换逻辑被触发
        self.mock_manager.set_scene.assert_called_with("menu")

    def test_small_window_with_long_copy_still_renders(self):
        self.mock_manager.t.side_effect = lambda key, **kwargs: {
            "onboarding.title": "30s Quick Start For Visual Training",
            "onboarding.subtitle": "Finish this once before your first training session to understand the posture, distance, response keys, and pacing tips.",
            "onboarding.tip1": "Sit upright, keep a stable viewing distance, and avoid glare from nearby windows or lamps.",
            "onboarding.tip2": "Use arrow keys to answer E direction and keep your shoulders relaxed during the task.",
            "onboarding.tip3": "Train 5-10 minutes per session, and stop early if your eyes feel too tired.",
            "onboarding.tip4": "This app is only a training aid and does not replace medical diagnosis or treatment.",
            "onboarding.estimate": "Recommended start: L4 / 20-30 questions / steady pace with short breaks if needed.",
            "onboarding.start": "I Understand",
            "onboarding.skip": "Skip",
        }.get(key, key)
        self.scene.on_resize(840, 640)
        frame = self.capture_frame(self.scene)
        center_color = self.get_surface_average_color(frame, (170, 120, 500, 320))
        self.assertGreater(sum(center_color[:3]), 10)


if __name__ == '__main__':
    unittest.main()
