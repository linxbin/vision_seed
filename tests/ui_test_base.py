import pygame
import unittest
from unittest.mock import Mock, MagicMock, patch
import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class UITestCase(unittest.TestCase):
    """
    UI测试基类，提供Pygame UI测试的基础功能
    """
    
    @classmethod
    def setUpClass(cls):
        """类级别初始化，确保Pygame正确初始化"""
        # 确保Pygame子系统正确初始化
        if not pygame.get_init():
            pygame.init()
        if not pygame.font.get_init():
            pygame.font.init()
    
    @classmethod
    def tearDownClass(cls):
        """类级别清理"""
        pygame.quit()
    
    def setUp(self):
        """每个测试用例的初始化"""
        # 创建测试用的Surface
        self.test_surface = pygame.Surface((900, 700))
        self.test_surface.fill((0, 0, 0))  # 黑色背景
        
        # 创建时钟用于控制帧率
        self.clock = pygame.time.Clock()
        
        # 清空事件队列
        pygame.event.clear()
        
        # 初始化鼠标位置mock
        self.mock_mouse_pos = (0, 0)
    
    def tearDown(self):
        """每个测试用例的清理"""
        pass
    
    def set_mouse_position(self, x, y):
        """设置模拟的鼠标位置"""
        self.mock_mouse_pos = (x, y)
    
    def simulate_key_event(self, key, mod=0):
        """
        模拟键盘事件
        
        Args:
            key: pygame按键常量 (如 pygame.K_UP)
            mod: 修饰键状态 (如 pygame.KMOD_SHIFT)
            
        Returns:
            list: 包含单个KEYDOWN事件的列表
        """
        event = pygame.event.Event(pygame.KEYDOWN, key=key, mod=mod)
        return [event]
    
    def simulate_keyup_event(self, key, mod=0):
        """
        模拟键盘释放事件
        
        Args:
            key: pygame按键常量
            mod: 修饰键状态
            
        Returns:
            list: 包含单个KEYUP事件的列表
        """
        event = pygame.event.Event(pygame.KEYUP, key=key, mod=mod)
        return [event]
    
    def simulate_mouse_event(self, event_type, pos, button=1):
        """
        模拟鼠标事件
        
        Args:
            event_type: pygame.MOUSEBUTTONDOWN, pygame.MOUSEBUTTONUP, pygame.MOUSEMOTION
            pos: 鼠标位置 (x, y)
            button: 鼠标按钮 (1=左键, 2=中键, 3=右键)
            
        Returns:
            list: 包含鼠标事件的列表
        """
        if event_type == pygame.MOUSEMOTION:
            event = pygame.event.Event(event_type, pos=pos, rel=(0, 0), buttons=(0, 0, 0))
        else:
            event = pygame.event.Event(event_type, pos=pos, button=button)
        return [event]
    
    def capture_frame(self, scene, events=None, update_count=1):
        """
        捕获场景的单帧渲染结果
        
        Args:
            scene: 要测试的场景实例
            events: 要处理的事件列表
            update_count: 更新次数（用于处理动画）
            
        Returns:
            pygame.Surface: 渲染后的Surface副本
        """
        # Mock pygame.mouse.get_pos() 以返回我们设置的位置
        with patch('pygame.mouse.get_pos', return_value=self.mock_mouse_pos):
            # 处理事件（在mock环境下）
            if events:
                scene.handle_events(events)
            
            # 执行多次更新（用于动画效果）
            for _ in range(update_count):
                scene.update()
            
            # 渲染到测试Surface（在mock环境下）
            scene.draw(self.test_surface)
        
        # 返回副本以避免后续修改影响
        return self.test_surface.copy()
    
    def assert_pixel_color(self, surface, x, y, expected_color, tolerance=10):
        """
        断言特定像素的颜色
        
        Args:
            surface: 要检查的Surface
            x, y: 像素坐标
            expected_color: 期望的颜色 (R, G, B) 或 (R, G, B, A)
            tolerance: 颜色容差值
        """
        # 检查坐标是否在Surface范围内
        if x < 0 or x >= surface.get_width() or y < 0 or y >= surface.get_height():
            self.fail(f"坐标 ({x}, {y}) 超出Surface范围 ({surface.get_width()}, {surface.get_height()})")
        
        actual_color = surface.get_at((x, y))
        expected_len = len(expected_color)
        
        # 比较RGB分量
        for i in range(min(3, expected_len)):
            self.assertAlmostEqual(
                actual_color[i], 
                expected_color[i], 
                delta=tolerance,
                msg=f"像素 ({x}, {y}) 的颜色分量 {['R', 'G', 'B'][i]} 不匹配: 期望 {expected_color[i]}, 实际 {actual_color[i]}"
            )
        
        # 如果提供了Alpha值，也进行比较
        if expected_len > 3 and len(actual_color) > 3:
            self.assertAlmostEqual(
                actual_color[3], 
                expected_color[3], 
                delta=tolerance,
                msg=f"像素 ({x}, {y}) 的Alpha值不匹配: 期望 {expected_color[3]}, 实际 {actual_color[3]}"
            )
    
    def get_surface_average_color(self, surface, rect=None):
        """
        获取Surface指定区域的平均颜色
        
        Args:
            surface: 要分析的Surface
            rect: 可选的矩形区域 (x, y, width, height)，如果为None则使用整个Surface
            
        Returns:
            tuple: 平均颜色 (R, G, B, A)
        """
        if rect is None:
            rect = (0, 0, surface.get_width(), surface.get_height())
        
        x, y, width, height = rect
        total_r = total_g = total_b = total_a = 0
        pixel_count = 0
        
        for px in range(x, x + width):
            for py in range(y, y + height):
                if px < surface.get_width() and py < surface.get_height():
                    color = surface.get_at((px, py))
                    total_r += color[0]
                    total_g += color[1]
                    total_b += color[2]
                    total_a += color[3]
                    pixel_count += 1
        
        if pixel_count == 0:
            return (0, 0, 0, 0)
        
        return (
            total_r // pixel_count,
            total_g // pixel_count,
            total_b // pixel_count,
            total_a // pixel_count
        )
    
    def create_mock_scene_manager(self):
        """
        创建模拟的SceneManager用于测试
        
        Returns:
            Mock: 模拟的SceneManager实例
        """
        mock_manager = Mock()
        mock_manager.settings = {
            "sound_enabled": True,
            "language": "en-US",
            "fullscreen": False,
            "total_questions": 30,
            "start_level": 3,
            "adaptive_enabled": True
        }
        
        # 模拟必要的管理器
        mock_manager.sound_manager = Mock()
        mock_manager.language_manager = Mock()
        mock_manager.data_manager = Mock()
        mock_manager.license_manager = Mock()
        mock_manager.adaptive_manager = Mock()
        mock_manager.preferences_manager = Mock()
        
        # 添加t()方法用于多语言支持，支持关键字参数
        def mock_t(key, **kwargs):
            """模拟语言翻译方法，支持格式化参数"""
            translations = {
                "training.pause_hint": "Press P to pause",
                "training.back_to_menu": "Back",
                "config.title": "Configuration",
                "config.difficulty": "Difficulty",
                "config.questions": "Questions",
                "config.start_training": "Start Training",
                "config.preview_level_size": "Level {level}: {size}px",
                "config.template_child": "Child",
                "config.template_adult": "Adult", 
                "config.template_recovery": "Recovery",
                "menu.title": "VisionSeed",
                "menu.subtitle": "Visual Training Application",
                "menu.start_training": "Start Training",
                "menu.configuration": "Configuration",
                "menu.view_history": "View History",
                "menu.exit": "Exit"
            }
            
            template = translations.get(key, f"MISSING:{key}")
            try:
                return template.format(**kwargs)
            except KeyError:
                # 如果格式化失败，返回原始模板
                return template
        
        mock_manager.t = mock_t
        
        # 添加屏幕尺寸方法
        mock_manager.set_screen_size = Mock()
        mock_manager.get_screen_size = Mock(return_value=(900, 700))
        
        # 添加apply_training_template方法
        mock_manager.apply_training_template = Mock()
        
        return mock_manager