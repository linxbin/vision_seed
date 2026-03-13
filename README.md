# VisionSeed

VisionSeed 是一个基于 Python + Pygame 的视觉训练应用。项目目标不是单一小游戏，而是提供一个可扩展的多游戏训练平台，统一承载分类导航、游戏接入、训练记录、多语言、授权和系统设置。

当前仓库的真实状态已经超过最初的 `v1.0.0` 文档基线，代码里现已接入多款训练游戏，并完成了多游戏架构、统一游戏宿主页、训练记录落盘、红蓝眼镜模式复用和本地授权流程。

## 当前已接入游戏

按分类统计，当前代码中已注册 9 个游戏：

- 调节训练
  - `accommodation.e_orientation`
  - `accommodation.catch_fruit`
- 同时视训练
  - `simultaneous.eye_find_patterns`
  - `simultaneous.spot_difference`
  - `simultaneous.pong`
- 融合训练
  - `fusion.push_box`
- 脱抑制训练
  - `suppression.weak_eye_key`
- 立体视训练
  - `stereopsis.depth_grab`
- 弱视训练
  - `amblyopia.precision_aim`

游戏注册位置见 [core/game_registry.py](/C:/workspace/python/vision_seed/core/game_registry.py)。

## 核心能力

- 多游戏平台架构：主菜单 -> 分类页 -> 游戏宿主页 -> 游戏内部流程
- 统一游戏接入协议：`GameDescriptor`
- 场景统一调度：`SceneManager + GameHostScene`
- 本地训练记录：按 `game_id` 命名空间保存
- 中英双语：`en-US` / `zh-CN`
- 系统设置：语言、音效、训练时长等
- 本地授权：设备绑定激活码校验
- 启动健康检查：音频或资源异常时降级启动
- 红蓝眼镜模式：公共滤镜、方向切换、统一色板

## 当前进度判断

从代码状态看，项目当前更接近：

- 平台层：已完成首版并可持续扩展
- 多游戏接入：已落地
- 内容覆盖：已有代表性样板，但仍未铺满完整内容矩阵
- 文档状态：本 README 已同步到当前代码状态，规划文档见 `docs/`

目前最成熟的游戏模块仍然是 `E Orientation Training`，但同时视和融合训练也已经形成了统一菜单、统一文案和统一红蓝模式基线。

## 运行环境

- Python 3.10+
- Windows 10/11
- 依赖见 `requirements.txt`

## 快速开始

```bash
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
python main.py
```

## 测试

```bash
python -m unittest discover -s tests -p "test_*.py"
python tests/run_ui_tests.py
```

## 项目结构

```text
assets/
core/
scenes/
games/
tests/
docs/
tools/
main.py
```

更具体的分层：

- `core/`：平台能力，如注册表、场景管理、语言、音效、授权、记录
- `scenes/`：主菜单、分类页、系统设置、授权页、首次引导、游戏宿主页
- `games/<category>/<game>/`：游戏自己的入口、文案、场景、服务
- `tests/`：按核心层、全局场景、游戏模块分层测试

## 数据位置

运行时数据默认写入：

- `%LOCALAPPDATA%/VisionSeed/data/records.json`
- `%LOCALAPPDATA%/VisionSeed/config/user_preferences.json`
- `%LOCALAPPDATA%/VisionSeed/license/license.json`

## 授权

项目包含本地授权流程。激活码采用设备绑定 token，入口和校验逻辑在 `core/license_manager.py`。

生成工具示例：

```bash
python tools/generate_license_token.py --license-id LIC_20260228_0001 --order-ref ORDER_001 --device-hash sha256:xxxxxxxx
```

## 打包

打包说明见 [Packaging_README.md](/C:/workspace/python/vision_seed/Packaging_README.md)。

## 下一步建议

- 继续统一现有游戏的最小产品标准
- 补多游戏主链路回归测试
- 再决定是否扩展下一款融合训练游戏
