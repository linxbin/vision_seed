# VisionSeed (视芽)

VisionSeed 是一个基于 Python + Pygame 的 E 字方向视觉训练应用，提供从配置、训练、报告到历史复盘的完整闭环。

当前仓库已发布初代版本标签：`v1.0.0`。

## 核心功能

- 训练闭环：菜单 -> 配置 -> 训练 -> 报告 -> 历史
- 四方向识别训练：`上/下/左/右`，键盘方向键作答
- 即时反馈：对错音效 + 粒子反馈 + 连击展示
- 训练结束体验：完成音（`assets/completed.wav`）+ 平滑过渡后进入报告
- 报告页演出：入场淡入、卡片分段出现、关键数值滚动
- 暂停友好：`P` 键或按钮暂停/继续，窗口失焦自动暂停
- 难度等级：10 级（`5px` 到 `85px`）
- 题量范围：`0-1000`（包含 0 题边界）
- 历史记录：本地 JSON 持久化，筛选/排序/分页查看
- 自适应难度（V1）：基于最近 3 次训练（正确率 + 单题耗时）自动调级，可开关
- 快捷训练模板：儿童/成人/恢复一键开训
- 多语言：`en-US` / `zh-CN`（中文优先使用 `assets/SimHei.ttf`）
- 首次引导：首次启动显示 30 秒快速上手页
- 启动健康检查：资源缺失或音频初始化失败时自动降级，不阻断启动
- 本地授权：设备绑定激活码校验（未激活进入授权页）

## 运行环境

- Python 3.10+（推荐 3.11+）
- Windows 10/11（当前主要面向 Windows 桌面）
- 依赖见 `requirements.txt`

## 快速开始

```bash
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
python main.py
```

## 快捷键

- 菜单：`1-7` 快速启动不同入口/模板
- 训练：方向键作答，`P` 暂停/继续，`Esc` 返回菜单
- 全屏：`F11` 或 `Alt+Enter` 切换，`Esc` 可退出全屏
- 配置：`Enter` 开训，`Ctrl+S` 保存返回，`M/L/A` 切换音效/语言/自适应

## 运行测试

```bash
python -m unittest discover -s tests -p "test_*.py"
```

## 项目结构

```text
├── assets/
│   ├── correct.wav
│   ├── wrong.wav
│   ├── completed.wav
│   └── SimHei.ttf
├── config/
│   ├── display.py
│   ├── game.py
│   ├── levels.py
│   └── user_preferences.example.json
├── core/
│   ├── adaptive_manager.py
│   ├── app_paths.py
│   ├── base_scene.py
│   ├── data_manager.py
│   ├── e_generator.py
│   ├── language_manager.py
│   ├── license_manager.py
│   ├── preferences_manager.py
│   ├── scene_manager.py
│   ├── sound_manager.py
│   └── startup_health.py
├── scenes/
│   ├── menu_scene.py
│   ├── license_scene.py
│   ├── onboarding_scene.py
│   ├── config_scene.py
│   ├── training_scene.py
│   ├── report_scene.py
│   └── history_scene.py
├── tests/
│   └── test_*.py
├── tools/
│   └── generate_license_token.py
├── Packaging_README.md
└── main.py
```

## 数据与文件位置

VisionSeed 运行时数据默认写入：

- `%LOCALAPPDATA%/VisionSeed/data/records.json`
- `%LOCALAPPDATA%/VisionSeed/config/user_preferences.json`
- `%LOCALAPPDATA%/VisionSeed/license/license.json`

训练记录格式（`schema_version=2`）包含：

- `timestamp`, `session_id`
- `difficulty_level`, `e_size_px`
- `total_questions`, `correct_count`, `wrong_count`
- `duration_seconds`, `accuracy_rate`

读取旧记录时会自动做兼容迁移与字段规范化。

## 授权码（交易层）

- 启动时校验本地授权；未激活则进入授权页
- 授权码格式为设备绑定 token：`VS1.*`
- 卖家侧可使用工具脚本生成：

```bash
python tools/generate_license_token.py --license-id LIC_20260228_0001 --order-ref ORDER_001 --device-hash sha256:xxxxxxxx
```

## 打包发布

请参考 [Packaging_README.md](Packaging_README.md)。

## 已知限制

- 当前测试主要覆盖核心逻辑与关键场景状态，不包含完整 UI 自动化回放。
- 若 `assets/SimHei.ttf` 缺失，中文字体会回退系统字体，显示效果依赖系统环境。
- 当前授权密钥策略为本地最小可落地方案，若仓库公开请评估更高强度的签发架构。

## 许可证

本项目仅供学习和非商业用途。
