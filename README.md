# VisionSeed (视芽)

VisionSeed 是一个基于 Python + Pygame 的 E 字方向视觉训练应用，提供配置、训练、报告和历史记录的完整闭环。

## 当前功能

- 训练模块：四方向识别（上/下/左/右），实时对错反馈（V/X + 音效）
- 难度系统：8 级（10px 到 80px）
- 题量配置：`0-1000`（含 0 题边界）
- 历史记录：本地 JSON 持久化、分页查看、手动刷新
- 用户偏好持久化：题量、难度、音效、语言、全屏
- 多语言：`en-US` / `zh-CN`，中文优先使用 `assets/SimHei.ttf`
- 启动健康检查：资源缺失和音频初始化失败时自动降级，不阻断启动
- 数据模型版本化：训练记录 `schema_version=2`，读取旧记录时自动兼容迁移
- 全屏快捷键：`F11` 或 `Alt+Enter`，`Esc` 退出全屏
- 连击系统：训练过程中统计连击，报告页展示最高连击

## 目录结构

```text
├── assets/
│   ├── correct.wav
│   ├── wrong.wav
│   └── SimHei.ttf
├── config/
│   ├── display.py
│   ├── game.py
│   ├── levels.py
│   └── user_preferences.example.json
├── data/                          # 运行时不再写入该目录
├── core/
│   ├── app_paths.py
│   ├── base_scene.py
│   ├── data_manager.py
│   ├── e_generator.py
│   ├── language_manager.py
│   ├── preferences_manager.py
│   ├── scene_manager.py
│   ├── sound_manager.py
│   └── startup_health.py
├── scenes/
│   ├── menu_scene.py
│   ├── config_scene.py
│   ├── training_scene.py
│   ├── report_scene.py
│   └── history_scene.py
├── tests/
│   ├── test_config_validation.py
│   ├── test_data_manager_io.py
│   └── test_training_scoring.py
└── main.py
```

## 快速开始

```bash
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
python main.py
```

## 运行测试

```bash
python -m unittest discover -s tests -p "test_*.py"
```

## 数据格式说明

### 训练记录

文件：`%LOCALAPPDATA%/VisionSeed/data/records.json`

顶层字段：

- `schema_version`：当前为 `2`
- `sessions`：训练会话数组（最新在前）

每条会话字段：

- `schema_version`
- `timestamp`（ISO 字符串）
- `session_id`
- `difficulty_level`（1-8）
- `e_size_px`
- `total_questions`
- `correct_count`
- `wrong_count`
- `duration_seconds`
- `accuracy_rate`（0-100）

兼容策略：读取旧记录时自动补齐缺失字段并规范化数据。

### 用户偏好

运行时文件：`%LOCALAPPDATA%/VisionSeed/config/user_preferences.json`（已加入 `.gitignore`）

模板文件：`config/user_preferences.example.json`

字段：

- `start_level`
- `total_questions`
- `sound_enabled`
- `language`（`en-US` 或 `zh-CN`）
- `fullscreen`（布尔值）

## 已知限制

- 当前测试集为最小回归集，覆盖关键逻辑但不包含完整 UI 自动化测试。
- 若 `assets/SimHei.ttf` 缺失，中文会回退系统字体，显示效果依赖系统环境。

## 许可证

本项目仅供学习和非商业用途。
