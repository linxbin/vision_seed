# AGENTS.md

## 项目概述

VisionSeed 是一个基于 Python + Pygame 的多游戏视觉训练应用，而不是单一小游戏。

当前总体架构为：

- `core/`：平台基础设施
- `scenes/`：全局公共页面
- `games/`：各训练游戏模块
- `tests/`：单元测试与 UI 回归测试

项目目前以 Windows 桌面端为主。

## 当前训练分类

除非用户明确要求调整产品分类，否则保持以下六个顶层分类稳定：

1. `accommodation`
2. `simultaneous`
3. `fusion`
4. `suppression`
5. `stereopsis`
6. `amblyopia`

## 当前已注册游戏

内置游戏统一通过以下入口注册：

- `core/game_registry.py`

当前代码库中的内置游戏为：

- `accommodation.e_orientation`
- `accommodation.catch_fruit`
- `accommodation.snake`
- `simultaneous.eye_find_patterns`
- `simultaneous.spot_difference`
- `simultaneous.pong`
- `fusion.push_box`
- `fusion.tetris`
- `fusion.path_fusion`
- `suppression.weak_eye_key`
- `suppression.find_same`
- `suppression.red_blue_catch`
- `stereopsis.depth_grab`
- `stereopsis.ring_flight`
- `amblyopia.precision_aim`
- `amblyopia.whack_a_mole`
- `amblyopia.fruit_slice`

新增或移除游戏时，必须同步更新注册表、i18n、指标标签与测试。

## 架构规则

### 1. 全局场景与游戏场景边界

`scenes/` 只放平台级全局页面，例如：

- 主菜单
- 分类页
- 系统设置
- 首次引导
- 授权页
- 游戏宿主页

不要把游戏私有页面放进 `scenes/`。

游戏私有页面应放在：

- `games/<category>/<game>/scenes/`

### 2. 游戏模块结构

新游戏应尽量遵循以下结构：

```text
games/<category>/<game>/
├─ game.py
├─ i18n.py
├─ scenes/
├─ services/
└─ assets/
```

优先复用现有模块模式，不要另起一套新结构。

### 3. 接入契约

游戏通过 `GameDescriptor` 接入。

不要绕过以下基础设施：

- `core/game_contract.py`
- `core/game_registry.py`
- `scenes/game_host_scene.py`

如果一个游戏内部包含多个页面，应在游戏模块内部自行路由，通常返回一个 `root_scene.py` 作为入口。

### 4. 数据与记录

训练数据必须按 `game_id` 隔离。

保存和读取记录时要遵守：

- 保留 `game_id`
- 不把单游戏历史与全局历史混用
- 优先把记录逻辑放在游戏私有 `services/` 中，而不是直接堆在页面层

相关基础设施：

- `core/data_manager.py`
- `core/scene_manager.py`

### 5. 国际化

全局文案放在：

- `core/language_manager.py`

游戏私有文案放在：

- `games/<category>/<game>/i18n.py`

如果游戏已有本地 `i18n.py`，不要继续把游戏私有文案塞回全局语言表。

## UI 与 UX 规则

### 1. 平台页面风格

平台页面使用共享亮色主题：

- `core/ui_theme.py`

以下页面应保持统一视觉语言：

- `menu_scene.py`
- `category_scene.py`
- `system_settings_scene.py`
- onboarding 与 license 页面

除非用户明确要求，不要重新引入深色全屏平台页。

### 2. 训练 HUD

训练页面应避免拥挤。

建议布局：

- 左上：进度或游戏计数
- 上中：倒计时或主要会话信息
- 右上：返回或次级状态

避免标签、按钮、提示文本互相遮挡。

### 3. 儿童友好交互

游戏交互主要围绕鼠标点击，键盘上/下/左/右方向键，空格键进行交互。

默认键位：

- 方向键：移动 / 导航
- `Space`：主要动作
- `Enter`：继续 / 确认
- `Esc`：返回

### 4. 红蓝眼镜模式

涉及红蓝眼镜训练时，复用现有实现方式：

- `games/simultaneous/eye_find_patterns`
- `games/common/anaglyph.py`

不要为每个游戏单独再造一套红蓝系统。

当前基线模式包括：

- normal mode
- glasses mode
- `left_red_right_blue`
- `left_blue_right_red`

设计上优先：

- 强红/强蓝只用于训练关键元素
- 辅助元素与背景尽量使用中性或弱化颜色
- 游戏布局参考现有训练模式，必须避免元素重叠，元素布局要合理美观

## 玩法规则

### 1. 训练目标优先

不要机械照搬传统小游戏。

应把玩法改造成训练壳层，使其满足：

- 视觉训练任务是主目标
- 游戏循环负责提供重复动机
- 交互足够简单，儿童也能稳定完成

### 2. 每个游戏只聚焦一个主训练目标

除非用户明确要求，不要把多个训练目标硬塞进同一个游戏。

例如：

- `catch_fruit`：调节训练
- `spot_difference` / `pong`：同时视训练
- `precision_aim`：弱视训练

### 3. 短时长与清反馈

游戏应具备：

- 短回合或短时长节奏
- 即时反馈
- 简单明确的成功 / 失败判定
- 清晰的下一步引导

## 测试规则

只要有实质性改动，就运行回归测试。

最低要求命令：

```bash
python -m unittest discover -s tests -p "test_*.py"
python tests/run_ui_tests.py
```

迭代单模块时先跑定向测试，收尾再跑全量回归。

如果修复涉及玩法或交互，代码和测试要同步更新。

## 编辑规则

- 优先做小而局部的改动，不做无必要的大重写。
- 先复用现有 helper、service、scene 模式，再考虑抽新抽象。
- 未经明确批准，不要删除面向用户的分类、游戏或产品流程。
- 不要回退仓库里与当前任务无关的现有改动。
- 保持 Windows 兼容性。

## 文档规则

行为变化后，如果相关文档受影响，就同步更新，尤其是：

- `README.md`

规划文档必须和真实实现保持对齐；如果某项还只是计划，文档里要明确写清楚。

## 推荐实施顺序

扩展项目时，优先遵循以下顺序：

1. 确认分类与训练目标
2. 创建或更新游戏模块
3. 注册游戏
4. 接入 i18n
5. 增补测试
6. 运行全量回归
7. 如有需要更新文档

## 推荐参考模块

优先参考以下模块：

- `games/accommodation/e_orientation`
- `games/simultaneous/eye_find_patterns`
- `games/simultaneous/spot_difference`
- `games/simultaneous/pong`
- `games/common/training_runtime/arcade_scene.py`

这些模块比旧实验代码更能代表当前项目方向。
