# AGENTS.md

## 项目简介

VisionSeed 是一个基于 Python + Pygame 的 Windows 视觉训练应用。
核心流程为：授权 -> 引导 -> 菜单 -> 配置 / 训练 / 报告 / 历史。
训练内容是识别不同方向和大小的 "E" 字，并保存训练结果。

## 技术栈

- Python 3.10+
- `pygame==2.5.2`
- `unittest`

## 常用命令

运行项目：

```bash
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
python main.py
```

运行测试：

```bash
python -m unittest discover -s tests -p "test_*.py"
```

## 目录说明

- `main.py`：程序入口，负责初始化、窗口管理、场景注册
- `config/`：全局配置，如窗口尺寸、难度、题量范围
- `core/`：核心逻辑，如场景管理、数据存储、偏好设置、授权、自适应难度
- `scenes/`：各个页面/场景，如菜单、配置、训练、报告、历史、授权、引导
- `tests/`：单元测试和场景相关测试
- `tools/`：辅助脚本，如授权码生成
- `assets/`：字体、音效等资源

## 关键约定

- `SceneManager.set_scene()` 对 `training` 场景会调用 `reset()`，不是 `on_enter()`；改动时不要破坏这个行为。
- 用户设置统一放在 `SceneManager.settings`，修改后通过 `save_user_preferences()` 持久化。
- 训练记录通过 `DataManager.save_training_session()` 写入。
- 窗口缩放和全屏切换主要在 `main.py` 处理，场景侧通过 `on_resize()` 响应。
- 运行时数据默认写入 `%LOCALAPPDATA%/VisionSeed/`，不要随意改回仓库内存储。

## 修改建议

- 优先做小而集中的改动，尽量不要跨 `core/` 和 `scenes/` 大范围重构。
- 涉及界面文案时，尽量沿用现有多语言机制，不要只改单一语言文本。
- 涉及授权逻辑时要谨慎，不要引入绕过校验的行为。
- 训练、暂停/恢复、0 题模式、全屏/缩放 都是容易回归的点，修改后要重点验证。
- 仓库内部分中文注释可能有编码显示问题；除非任务就是修复编码，否则不要批量改编码。

## 测试建议

- 修改核心逻辑、场景切换、输入处理、持久化时，优先跑完整测试。
- 新增测试时继续使用 `unittest` 和 `test_*.py` 命名。
- Pygame 相关测试尽量保持可无界面运行、结果稳定。

## 建议阅读顺序

1. `README.md`
2. `main.py`
3. `core/scene_manager.py`
4. 对应功能所在的 `core/` 或 `scenes/` 文件
5. 对应的 `tests/`
