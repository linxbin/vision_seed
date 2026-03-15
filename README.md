# VisionSeed

VisionSeed 是一个基于 Python + Pygame 的视觉训练平台，不是单一小游戏项目。  
它的目标是用统一的平台层承载多种视觉训练分类，包括：

- 调节训练
- 同时视训练
- 融合视训练
- 脱抑制训练
- 立体视训练
- 弱视训练

当前仓库已经不是早期原型，而是一个具备：

- 多游戏平台架构
- 游戏注册与分类导航
- 主菜单 / 分类页 / 游戏宿主页
- 系统设置 / 多语言 / 本地训练记录
- 本地授权
- Windows 打包链路
- 多款已接入训练游戏

的桌面训练应用。

## 当前真实进度

截至当前代码状态，项目已经接入 18 款游戏，每个训练分类至少 3 款：

- 调节训练
  - `accommodation.e_orientation`
  - `accommodation.catch_fruit`
  - `accommodation.snake`
- 同时视训练
  - `simultaneous.eye_find_patterns`
  - `simultaneous.spot_difference`
  - `simultaneous.pong`
- 融合视训练
  - `fusion.push_box`
  - `fusion.tetris`
  - `fusion.path_fusion`
- 脱抑制训练
  - `suppression.weak_eye_key`
  - `suppression.find_same`
  - `suppression.red_blue_catch`
- 立体视训练
  - `stereopsis.depth_grab`
  - `stereopsis.brick_breaker`
  - `stereopsis.frogger`
- 弱视训练
  - `amblyopia.precision_aim`
  - `amblyopia.whack_a_mole`
  - `amblyopia.fruit_slice`

注册位置见：
[core/game_registry.py](/C:/workspace/python/vision_seed/core/game_registry.py)

这意味着项目当前阶段的重点已经不是“搭平台”，而是：

- 提升新增游戏完成度
- 统一训练目标表达
- 继续补 UI / 交互 / 红蓝模式细节
- 为上线做更完整的试玩与验收

## 适合后续 AI 接手时的项目判断

如果你是用其他 AI 产品继续跟进这个项目，建议先按下面的判断理解代码库：

- 平台层已经基本成型，不要轻易重做总架构。
- 新增游戏优先遵守现有 `GameDescriptor + GameHostScene + game_id` 体系。
- 游戏间最常见的改动不是主循环，而是：
  - 帮助页
  - HUD 布局
  - 红蓝模式渲染
  - 训练目标表达
  - 结果页指标
  - 训练记录字段
- 当前最容易出问题的区域是：
  - 红蓝模式性能
  - 全屏适配
  - HUD 重叠
  - 中文文案遗漏或回退成 key
  - 返回链路不一致

## 架构概览

### 1. 平台层

- [main.py](/C:/workspace/python/vision_seed/main.py)
  应用入口，初始化 Pygame、SceneManager、全局场景并进入主循环。
- [core/scene_manager.py](/C:/workspace/python/vision_seed/core/scene_manager.py)
  全局状态中心，管理场景切换、设置、语言、声音、记录、授权、注册表等。
- [core/game_registry.py](/C:/workspace/python/vision_seed/core/game_registry.py)
  内建游戏注册表，按分类返回游戏。
- [core/language_manager.py](/C:/workspace/python/vision_seed/core/language_manager.py)
  平台与游戏文案的统一合并入口。
- [core/data_manager.py](/C:/workspace/python/vision_seed/core/data_manager.py)
  训练记录持久化。
- [core/license_manager.py](/C:/workspace/python/vision_seed/core/license_manager.py)
  本地授权逻辑。

### 2. 全局场景层

- [scenes/menu_scene.py](/C:/workspace/python/vision_seed/scenes/menu_scene.py)
- [scenes/category_scene.py](/C:/workspace/python/vision_seed/scenes/category_scene.py)
- [scenes/game_host_scene.py](/C:/workspace/python/vision_seed/scenes/game_host_scene.py)
- [scenes/system_settings_scene.py](/C:/workspace/python/vision_seed/scenes/system_settings_scene.py)
- [scenes/license_scene.py](/C:/workspace/python/vision_seed/scenes/license_scene.py)
- [scenes/onboarding_scene.py](/C:/workspace/python/vision_seed/scenes/onboarding_scene.py)

### 3. 游戏层

每款游戏按下面结构组织：

```text
games/<category>/<game>/
  game.py
  i18n.py
  scenes/
  services/
```

接入协议见：
[core/game_contract.py](/C:/workspace/python/vision_seed/core/game_contract.py)

### 4. 公共训练运行时

历史上的 `arcade_training` 已迁到：
[games/common/training_runtime](/C:/workspace/python/vision_seed/games/common/training_runtime)

当前它的定位是“公共训练运行时能力层”，不是新的大模板。  
后续开发应优先：

- 让每个游戏保持自己的 `root_scene.py`
- 只把真正通用的 session / scoring / feedback / widgets 放进 `training_runtime`

## 当前游戏完成度判断

### 标杆或接近标杆

- [games/accommodation/e_orientation](/C:/workspace/python/vision_seed/games/accommodation/e_orientation)
- [games/simultaneous/eye_find_patterns](/C:/workspace/python/vision_seed/games/simultaneous/eye_find_patterns)
- [games/fusion/push_box](/C:/workspace/python/vision_seed/games/fusion/push_box)
- [games/suppression/weak_eye_key](/C:/workspace/python/vision_seed/games/suppression/weak_eye_key)
- [games/stereopsis/depth_grab](/C:/workspace/python/vision_seed/games/stereopsis/depth_grab)

### 已接入但仍需持续打磨

- [games/simultaneous/spot_difference](/C:/workspace/python/vision_seed/games/simultaneous/spot_difference)
- [games/simultaneous/pong](/C:/workspace/python/vision_seed/games/simultaneous/pong)
- [games/stereopsis/brick_breaker](/C:/workspace/python/vision_seed/games/stereopsis/brick_breaker)
- [games/stereopsis/frogger](/C:/workspace/python/vision_seed/games/stereopsis/frogger)
- [games/fusion/tetris](/C:/workspace/python/vision_seed/games/fusion/tetris)
- [games/fusion/path_fusion](/C:/workspace/python/vision_seed/games/fusion/path_fusion)
- [games/suppression/find_same](/C:/workspace/python/vision_seed/games/suppression/find_same)
- [games/suppression/red_blue_catch](/C:/workspace/python/vision_seed/games/suppression/red_blue_catch)
- [games/amblyopia/precision_aim](/C:/workspace/python/vision_seed/games/amblyopia/precision_aim)
- [games/amblyopia/whack_a_mole](/C:/workspace/python/vision_seed/games/amblyopia/whack_a_mole)
- [games/amblyopia/fruit_slice](/C:/workspace/python/vision_seed/games/amblyopia/fruit_slice)
- [games/accommodation/catch_fruit](/C:/workspace/python/vision_seed/games/accommodation/catch_fruit)
- [games/accommodation/snake](/C:/workspace/python/vision_seed/games/accommodation/snake)

这部分仍然是后续打磨重点。

## 红蓝模式的当前约束

当前项目里，红蓝模式不应只是“换颜色按钮”，而应满足：

- 支持 `Left Red / Right Blue`
- 支持 `Left Blue / Right Red`
- 左右眼方向切换必须真实影响渲染结果
- 新游戏优先复用：
  - [games/common/anaglyph.py](/C:/workspace/python/vision_seed/games/common/anaglyph.py)
  - [games/simultaneous/eye_find_patterns](/C:/workspace/python/vision_seed/games/simultaneous/eye_find_patterns)
  的交互口径

最近已经修过一轮新增游戏红蓝模式性能问题。后续如果红蓝模式“速度一样但看起来卡”，首先检查是不是在做整屏离屏层 + `surfarray` 合成。

## 训练记录与数据位置

运行数据默认写入：

- `%LOCALAPPDATA%/VisionSeed/data/records.json`
- `%LOCALAPPDATA%/VisionSeed/config/user_preferences.json`
- `%LOCALAPPDATA%/VisionSeed/license/license.json`

记录按 `game_id` 命名空间隔离。  
后续新增训练指标时，建议同步检查：

- [core/game_metrics.py](/C:/workspace/python/vision_seed/core/game_metrics.py)
- 对应游戏 `i18n.py`

否则菜单与分类页的“最新训练报告”容易显示原始 key。

## 测试现状

当前仓库已有较完整的自动化回归，建议把它当作开发基线的一部分，而不是可选项。

常用命令：

```bash
python -m unittest discover -s tests -t . -p "test_*.py"
python tests/run_ui_tests.py
```

新增或修改游戏时，至少补：

- 游戏专项测试
- 结果保存测试
- 红蓝模式方向切换测试
- 返回链路测试
- 全屏 / resize 相关测试（如果场景自定义布局）

## 运行环境

- Python 3.10+
- Windows 10/11
- 依赖见 [requirements.txt](/C:/workspace/python/vision_seed/requirements.txt)

快速开始：

```bash
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
python main.py
```

## 打包与授权

- 打包说明见 [Packaging_README.md](/C:/workspace/python/vision_seed/Packaging_README.md)
- 授权逻辑见 [core/license_manager.py](/C:/workspace/python/vision_seed/core/license_manager.py)
- 授权生成工具示例：

```bash
python tools/generate_license_token.py --license-id LIC_20260228_0001 --order-ref ORDER_001 --device-hash sha256:xxxxxxxx
```

## 当前最值得继续推进的工作

如果后续继续开发，优先级建议如下：

1. 做一轮完整人工试玩
   重点看：
   - HUD 是否遮挡
   - 红蓝模式是否稳定
   - 全屏适配是否一致
   - 返回链路是否统一
2. 收口新增游戏完成度
   尤其是：
   - `brick_breaker`
   - `frogger`
   - `tetris`
   - `path_fusion`
   - `red_blue_catch`
3. 统一结果页与训练指标
   让菜单摘要、分类摘要和结果页表达一致
4. 做上线前验收
   包括：
   - 文案走查
   - 试玩反馈
   - 打包验证
   - 授权流程验证

## 项目目录

```text
assets/
core/
docs/
games/
scenes/
tests/
tools/
main.py
visionseed.spec
Packaging_README.md
```

## 备注

用于规划新游戏的文档仍在 `docs/` 中。  
其中 [视觉训练小游戏分类指南.md](/C:/workspace/python/vision_seed/docs/视觉训练小游戏分类指南.md) 应继续作为“设计与选题指南”使用，不应再当作“实时项目进度记录”。
