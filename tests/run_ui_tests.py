#!/usr/bin/env python3
"""
UI测试运行器
用于运行所有UI相关的自动化测试
"""

import unittest
import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def discover_and_run_ui_tests():
    """发现并运行所有UI测试"""
    # 创建测试套件
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # 添加所有UI测试模块
    ui_test_modules = [
        'test_training_scene_ui',
        'test_config_scene_ui',
        'test_menu_scene_ui',
        'test_report_scene_ui',
        'test_history_scene_ui',
        'test_onboarding_scene_ui',
        'test_license_scene_ui'
    ]
    
    for module_name in ui_test_modules:
        try:
            module = __import__(f'tests.{module_name}', fromlist=[''])
            tests = loader.loadTestsFromModule(module)
            suite.addTests(tests)
            print(f"✓ 已添加测试模块: {module_name}")
        except ImportError as e:
            print(f"✗ 无法导入测试模块 {module_name}: {e}")
        except Exception as e:
            print(f"✗ 加载测试模块 {module_name} 时出错: {e}")
    
    if suite.countTestCases() == 0:
        print("⚠️  没有找到任何UI测试用例")
        return False
    
    # 运行测试
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return result.wasSuccessful()


if __name__ == '__main__':
    success = discover_and_run_ui_tests()
    sys.exit(0 if success else 1)