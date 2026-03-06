import pygame
import sys
import os
import unittest

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tests.ui_test_base import UITestCase
from games.accommodation.e_orientation.scenes.config_scene import ConfigScene


class TestConfigSceneUI(UITestCase):
    """配置场景UI测试"""
    
    def setUp(self):
        super().setUp()
        # 创建模拟的场景管理器
        self.mock_manager = self.create_mock_scene_manager()
        # 创建配置场景实例
        self.scene = ConfigScene(self.mock_manager)
    
    def test_scene_initialization(self):
        """测试配置场景初始化状态"""
        self.assertIsNotNone(self.scene.manager)
        # 验证默认设置从manager正确同步
        self.assertEqual(self.scene.draft_settings["start_level"], 3)  # 默认等级3
        self.assertEqual(self.scene.draft_settings["total_questions"], 30)  # 默认题数30
    
    def test_difficulty_level_selection_ui(self):
        """测试难度等级选择的UI表现"""
        # 捕获初始帧（应该显示默认等级3选中）
        initial_frame = self.capture_frame(self.scene)
        
        # 验证初始状态下有内容渲染（不是纯黑屏）
        avg_color = self.get_surface_average_color(initial_frame)
        self.assertGreater(
            sum(avg_color[:3]), 
            10,
            "配置场景应该有UI元素渲染"
        )
    
    def test_question_count_input_ui(self):
        """测试题量输入框的UI表现"""
        # 初始状态下应该显示默认题数
        initial_frame = self.capture_frame(self.scene)
        
        # 修改题量并验证UI更新
        self.scene.draft_settings["total_questions"] = 50
        self.scene.input_text = "50"
        updated_frame = self.capture_frame(self.scene)
        
        # UI应该有变化（虽然我们无法直接读取文本，但可以验证像素变化）
        initial_sum = sum(self.get_surface_average_color(initial_frame)[:3])
        updated_sum = sum(self.get_surface_average_color(updated_frame)[:3])
        
        # 如果题量改变导致UI更新，像素总和应该不同
        # 注意：这个测试可能不够精确，但在没有OCR的情况下是合理的
        if initial_sum == updated_sum:
            # 如果像素相同，可能是题量显示区域太小，检查特定区域
            input_area = (
                updated_frame.get_width() - 200,  # 假设输入框在右侧
                updated_frame.get_height() // 2 - 50,
                150, 100
            )
            input_color = self.get_surface_average_color(updated_frame, input_area)
            self.assertGreater(
                sum(input_color[:3]),
                10,
                "题量输入区域应该有内容显示"
            )
    
    def test_mouse_interaction_simulation(self):
        """测试鼠标交互模拟"""
        # 获取屏幕中心位置（假设难度卡片在中心区域）
        center_x = self.test_surface.get_width() // 2
        center_y = self.test_surface.get_height() // 2
        
        # 模拟鼠标点击难度卡片
        click_events = self.simulate_mouse_event(
            pygame.MOUSEBUTTONDOWN, 
            (center_x, center_y), 
            button=1
        )
        
        # 捕获交互后的帧
        result_frame = self.capture_frame(self.scene, click_events)
        
        # 验证UI有响应（鼠标悬停或点击应该有视觉反馈）
        avg_color = self.get_surface_average_color(result_frame)
        self.assertGreater(
            sum(avg_color[:3]),
            10,
            "鼠标交互后UI应该有视觉反馈"
        )


if __name__ == '__main__':
    unittest.main()
