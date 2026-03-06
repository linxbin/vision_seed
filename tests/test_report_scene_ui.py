import pygame
import sys
import os
import unittest
from unittest.mock import patch

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tests.ui_test_base import UITestCase
from games.accommodation.e_orientation.scenes.report_scene import ReportScene


class TestReportSceneUI(UITestCase):
    """报告场景UI测试"""
    
    def setUp(self):
        super().setUp()
        # 创建模拟的场景管理器
        self.mock_manager = self.create_mock_scene_manager()
        # 设置模拟的训练结果
        self.mock_manager.current_result = {
            "correct": 25,
            "wrong": 5,
            "total": 30,
            "duration": 120.5,
            "max_combo": 8
        }
        # 模拟数据管理器返回历史记录
        self.mock_manager.data_manager.get_all_sessions.return_value = [
            {"timestamp": "2026-03-02T13:00:00", "accuracy_rate": 83.3},
            {"timestamp": "2026-03-02T12:00:00", "accuracy_rate": 75.0}
        ]
        # 模拟自适应评估
        self.mock_manager.evaluate_adaptive_level.return_value = {"suggested_level": 4, "reason": "improved"}
        # 创建报告场景实例
        self.scene = ReportScene(self.mock_manager)
        # 调用on_enter以初始化数据
        self.scene.on_enter()
    
    def test_scene_initialization(self):
        """测试报告场景初始化状态"""
        self.assertIsNotNone(self.scene.manager)
        self.assertEqual(len(self.scene.cards), 6)  # 6个数据卡片
        self.assertIsNotNone(self.scene.retry_button_rect)
        self.assertIsNotNone(self.scene.menu_button_rect)
        
        # 验证结果数据正确传递
        self.assertEqual(self.scene.final_result["correct"], 25)
        self.assertEqual(self.scene.final_result["total"], 30)
    
    def test_report_rendering_basic(self):
        """测试报告的基本渲染"""
        frame = self.capture_frame(self.scene)
        
        # 获取屏幕中心区域的平均颜色（应该有报告内容渲染）
        center_x = frame.get_width() // 2
        center_y = frame.get_height() // 2
        
        center_color = self.get_surface_average_color(
            frame, 
            (center_x - 150, center_y - 150, 300, 300)
        )
        
        # 报告应该有内容渲染（不是纯黑屏）
        self.assertGreater(
            sum(center_color[:3]), 
            10,
            f"报告场景未正确渲染，实际RGB总和: {sum(center_color[:3])}"
        )
    
    def test_data_card_display(self):
        """测试数据卡片的显示"""
        # 捕获报告帧
        frame = self.capture_frame(self.scene)
        
        # 验证关键数据是否显示（通过像素变化检测）
        # 正确答案数应该显示为25
        initial_sum = sum(self.get_surface_average_color(frame)[:3])
        
        # 修改结果数据并重新调用on_enter
        self.mock_manager.current_result["correct"] = 30
        self.scene.on_enter()  # 重新初始化数据
        updated_frame = self.capture_frame(self.scene)
        updated_sum = sum(self.get_surface_average_color(updated_frame)[:3])
        
        # 数据变化应该导致UI变化
        if initial_sum == updated_sum:
            # 如果像素相同，检查动画进度（可能动画还没完成）
            # 强制完成动画
            with patch('time.time', return_value=self.scene.enter_started_at + 10):
                final_frame = self.capture_frame(self.scene)
                final_sum = sum(self.get_surface_average_color(final_frame)[:3])
                self.assertNotEqual(
                    initial_sum,
                    final_sum,
                    "数据卡片应该随结果数据变化而更新"
                )
        else:
            self.assertNotEqual(
                initial_sum,
                updated_sum,
                "数据卡片应该随结果数据变化而更新"
            )
    
    def test_button_interaction(self):
        """测试按钮交互"""
        # 设置鼠标位置在重试按钮上
        retry_pos = (
            self.scene.retry_button_rect.centerx,
            self.scene.retry_button_rect.centery
        )
        self.set_mouse_position(*retry_pos)
        
        # 模拟点击重试按钮
        click_events = self.simulate_mouse_event(
            pygame.MOUSEBUTTONDOWN,
            retry_pos,
            button=1
        )
        
        # 捕获点击后的帧
        result_frame = self.capture_frame(self.scene, click_events)
        
        # 验证场景切换逻辑被触发
        self.mock_manager.set_scene.assert_called_with("training")


if __name__ == '__main__':
    unittest.main()
