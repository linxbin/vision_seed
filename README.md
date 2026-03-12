# VisionSeed (视芽)

VisionSeed 是一个基于 Python + Pygame 的多游戏视觉训练应用，提供主菜单、分类导航、游戏内流程和系统设置等完整闭环。

当前仓库已发布初代版本标签：`v1.0.0`。

## 核心功能

- 多游戏流程：主菜单 -> 分类 -> 游戏入口/游戏内菜单 -> 训练流程
- E 方向训练：配置、训练、报告、历史完整闭环
- 双眼找图案：裸眼/红蓝眼镜两种模式，含帮助页与结算页
- 即时反馈：对错音效、粒子反馈、连击展示
- 暂停友好：支持暂停/继续，窗口失焦自动暂停
- 难度等级：10 级（`5px` 到 `85px`）
- 历史记录：本地 JSON 持久化，筛选/排序/分页查看
- 自适应难度（V1）：基于最近 3 次训练自动调级，可开关
- 系统设置：全局语言/音效集中管理
- 多语言：`en-US` / `zh-CN`，游戏文案按模块拆分
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
venv\Scriptsctivate
pip install -r requirements.txt
python main.py
```

## 快捷键

- 主菜单：`1-9` 选择分类/系统设置/退出
- 游戏内菜单（E方向训练）：`1-4` 选择训练/配置/历史/返回
- 训练：方向键作答，`P` 暂停/继续，`Esc` 返回游戏内菜单
- 全屏：`F11` 或 `Alt+Enter` 切换，`Esc` 可退出全屏
- 配置（E方向训练）：`Enter` 开训，`Ctrl+S` 保存返回，`A` 切换自适应
- 系统设置：`1` 切换音效，`2` 切换语言，`Esc` 返回主菜单

## 运行测试

```bash
python -m unittest discover -s tests -p "test_*.py"
python tests/run_ui_tests.py
```

## 项目结构

```text
├── assets/
├── config/
├── core/
│   ├── game_contract.py
│   ├── game_registry.py
│   ├── language_manager.py
│   ├── scene_manager.py
│   └── ...
├── scenes/
│   ├── menu_scene.py
│   ├── category_scene.py
│   ├── system_settings_scene.py
│   ├── license_scene.py
│   ├── onboarding_scene.py
│   └── game_host_scene.py
├── games/
│   ├── accommodation/
│   │   └── e_orientation/
│   │       ├── game.py
│   │       ├── i18n.py
│   │       ├── scenes/
│   │       ├── services/
│   │       └── README.md
│   └── simultaneous/
│       └── eye_find_patterns/
│           ├── game.py
│           ├── i18n.py
│           ├── scenes/
│           ├── services/
│           └── README.md
├── tests/
│   ├── core/
│   ├── scenes/
│   └── games/
├── docs/
├── tools/
└── main.py
```

## 架构说明

- `core/` 只放平台能力和公共基础设施。
- `scenes/` 只放全局公共页面，不放具体游戏私有页面。
- `games/<category>/<game>/` 存放游戏自己的入口、文案、场景和服务。
- 游戏名称和私有文案优先放在各自 `i18n.py`，由 `LanguageManager` 合并加载。
- 多页面游戏通过各自的 `root_scene.py` 管理内部路由，`GameHostScene` 仅负责挂载游戏根场景。
- `DataManager` 通过 `game_id` 命名空间读取训练记录，游戏优先通过各自的 `services/` 访问记录和规则。

## 数据与文件位置

VisionSeed 运行时数据默认写入：

- `%LOCALAPPDATA%/VisionSeed/data/records.json`
- `%LOCALAPPDATA%/VisionSeed/config/user_preferences.json`
- `%LOCALAPPDATA%/VisionSeed/license/license.json`

训练记录格式（`schema_version=3`）包含：

- `timestamp`, `session_id`
- `game_id`
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
