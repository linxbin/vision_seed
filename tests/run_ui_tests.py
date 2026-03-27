#!/usr/bin/env python3
"""
UI测试运行器
用于运行所有UI相关的自动化测试
"""

import importlib.util
import os
import sys
import unittest
from pathlib import Path

# 添加项目根目录到Python路径
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


UI_TEST_FILES = [
    "scenes/test_category_scene_ui.py",
    "scenes/test_menu_scene_ui.py",
    "scenes/test_system_settings_scene.py",
    "scenes/test_onboarding_scene_ui.py",
    "scenes/test_license_scene_ui.py",
    "games/accommodation/e_orientation/test_training_scene_ui.py",
    "games/accommodation/e_orientation/test_config_scene_ui.py",
    "games/accommodation/e_orientation/test_report_scene_ui.py",
    "games/accommodation/e_orientation/test_history_scene_ui.py",
]


def _load_module_from_path(path: Path, module_name: str):
    spec = importlib.util.spec_from_file_location(module_name, path)
    if spec is None or spec.loader is None:
        raise ImportError(f"无法为 {path} 创建导入规格")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def discover_and_run_ui_tests():
    """发现并运行所有UI测试"""
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    for index, rel_path in enumerate(UI_TEST_FILES, start=1):
        file_path = ROOT / 'tests' / rel_path
        module_name = f"ui_test_module_{index}"
        try:
            module = _load_module_from_path(file_path, module_name)
            tests = loader.loadTestsFromModule(module)
            suite.addTests(tests)
            print(f"[OK] 已添加测试模块: {rel_path}")
        except ImportError as e:
            print(f"[ERR] 无法导入测试模块 {rel_path}: {e}")
        except Exception as e:
            print(f"[ERR] 加载测试模块 {rel_path} 时出错: {e}")

    if suite.countTestCases() == 0:
        print("[WARN] 没有找到任何UI测试用例")
        return False

    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    return result.wasSuccessful()


if __name__ == '__main__':
    success = discover_and_run_ui_tests()
    sys.exit(0 if success else 1)
