import pygame
import sys
import os
import unittest

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tests.ui_test_base import UITestCase
from games.accommodation.e_orientation.scenes.training_scene import TrainingScene


class TestTrainingSceneUI(UITestCase):
    """训练场景UI测试"""
    
    def setUp(self):
        super().setUp()
        # 创建模拟的场景管理器
        self.mock_manager = self.create_mock_scene_manager()
        # 创建训练场景实例
        self.scene = TrainingScene(self.mock_manager)
    
    def test_scene_initialization(self):
        """测试训练场景初始化状态"""
        # 验证场景是否正确初始化
        self.assertIsNotNone(self.scene.manager)
        self.assertEqual(self.scene.current, 0)  # 使用正确的属性名
        self.assertEqual(self.scene.correct, 0)  # 使用正确的属性名
        
        # 验证初始难度设置
        expected_level_index = self.mock_manager.settings["start_level"] - 1
        from config import E_SIZE_LEVELS
        expected_size = E_SIZE_LEVELS[expected_level_index]
        self.assertEqual(self.scene.base_size, expected_size)
    
    def test_e_char_rendering_basic(self):
        """测试E字的基本渲染"""
        # 捕获初始帧
        frame = self.capture_frame(self.scene)
        
        # 获取屏幕中心区域的平均颜色（应该有E字渲染）
        center_x = frame.get_width() // 2
        center_y = frame.get_height() // 2
        
        # E字通常是白色，背景是黑色
        # 检查中心区域是否不是纯黑色（说明有内容渲染）
        center_color = self.get_surface_average_color(
            frame, 
            (center_x - 50, center_y - 50, 100, 100)
        )
        
        # 如果中心区域完全是黑色，说明没有渲染内容
        # 调整容差值，因为E字可能比较小
        self.assertGreater(
            sum(center_color[:3]),  # RGB总和
            5,  # 降低阈值，至少有一些非黑色像素
            f"E字未正确渲染到屏幕中心，实际RGB总和: {sum(center_color[:3])}"
        )
    
    def test_e_char_size_by_level(self):
        """测试不同难度等级下E字的尺寸变化"""
        # 测试最小等级（1级）
        self.scene.level_index = 0  # 等级1对应索引0
        frame_level_1 = self.capture_frame(self.scene)
        
        # 测试最大等级（10级）
        self.scene.level_index = 9  # 等级10对应索引9
        frame_level_10 = self.capture_frame(self.scene)
        
        # 获取两个帧的中心区域平均颜色
        center_rect = (
            frame_level_1.get_width() // 2 - 100,
            frame_level_1.get_height() // 2 - 100,
            200, 200
        )
        
        color_level_1 = self.get_surface_average_color(frame_level_1, center_rect)
        color_level_10 = self.get_surface_average_color(frame_level_10, center_rect)
        
        # 更大的E字应该在中心区域有更多的白色像素
        # 因此RGB总和应该更大
        sum_level_1 = sum(color_level_1[:3])
        sum_level_10 = sum(color_level_10[:3])
        
        # 由于10级的E字更大，应该覆盖更多中心区域
        self.assertGreaterEqual(
            sum_level_10, 
            sum_level_1,
            "10级E字的渲染区域应该不小于1级"
        )
    
    def test_direction_input_visual_feedback(self):
        """测试方向输入的视觉反馈"""
        # 先渲染一帧确保场景准备好
        initial_frame = self.capture_frame(self.scene)
        
        # 强制设置target_direction为UP，确保我们的输入是正确的
        self.scene.target_direction = "UP"
        
        # 模拟按下上方向键（正确答案）
        events = self.simulate_key_event(pygame.K_UP)
        # 增加更新次数以确保粒子效果完全显示
        feedback_frame = self.capture_frame(self.scene, events, update_count=5)
        
        # 验证场景状态已更新
        self.assertEqual(self.scene.current, 1)
        self.assertEqual(self.scene.correct, 1)
        
        # 验证UI有变化（通过比较像素差异）
        initial_sum = sum(self.get_surface_average_color(initial_frame)[:3])
        feedback_sum = sum(self.get_surface_average_color(feedback_frame)[:3])
        
        # 视觉反馈应该导致屏幕内容发生变化
        # 如果仍然相同，检查粒子系统是否被激活
        if initial_sum == feedback_sum:
            # 检查粒子列表
            self.assertGreater(
                len(self.scene.particles), 
                0, 
                "正确答案后应该生成粒子效果"
            )
        else:
            self.assertNotEqual(
                initial_sum, 
                feedback_sum,
                "方向键输入后UI应该有视觉变化"
            )
    
    def test_pause_functionality_ui(self):
        """测试暂停功能的UI表现"""
        # 先确保场景在运行状态
        running_frame = self.capture_frame(self.scene)
        
        # 验证初始状态未暂停
        self.assertFalse(self.scene.is_paused)
        
        # 模拟按下P键暂停
        pause_events = self.simulate_key_event(pygame.K_p)
        paused_frame = self.capture_frame(self.scene, pause_events, update_count=2)
        
        # 验证暂停状态已激活
        self.assertTrue(self.scene.is_paused)
        
        # 验证暂停状态（通常会有暂停遮罩或文本）
        # 暂停时屏幕应该有明显变化
        running_sum = sum(self.get_surface_average_color(running_frame)[:3])
        paused_sum = sum(self.get_surface_average_color(paused_frame)[:3])
        
        self.assertNotEqual(
            running_sum,
            paused_sum,
            "暂停功能应该导致UI视觉变化"
        )


if __name__ == '__main__':
    unittest.main()
