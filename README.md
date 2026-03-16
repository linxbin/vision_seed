# VisionSeed

VisionSeed 是一个基于 Python + Pygame 的多游戏视觉训练平台，而不是单一小游戏项目。  
项目以统一的平台层承载多个训练分类，当前稳定保留六个顶层分类：

- `accommodation`
- `simultaneous`
- `fusion`
- `suppression`
- `stereopsis`
- `amblyopia`

## 当前状态

当前代码库已接入 18 个内置训练游戏，注册位置见 [core/game_registry.py](/C:/workspace/python/vision_seed/core/game_registry.py)。

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
- `stereopsis.brick_breaker`
- `stereopsis.frogger`
- `amblyopia.precision_aim`
- `amblyopia.whack_a_mole`
- `amblyopia.fruit_slice`

平台页目前已统一到共享亮色主题，核心样式见 [core/ui_theme.py](/C:/workspace/python/vision_seed/core/ui_theme.py)。  
主菜单、分类页、系统设置、首次引导、授权页使用统一平台语言；主要自定义训练页也已完成一轮 HUD 和结果页布局收口。

当前自动化回归状态：

- `python -m unittest discover -s tests -p "test_*.py"` 通过
- `python tests/run_ui_tests.py` 通过

## 架构概览

### 平台层

- [main.py](/C:/workspace/python/vision_seed/main.py)：应用入口
- [core/scene_manager.py](/C:/workspace/python/vision_seed/core/scene_manager.py)：全局场景与应用状态
- [core/game_registry.py](/C:/workspace/python/vision_seed/core/game_registry.py)：游戏注册与分类查询
- [core/language_manager.py](/C:/workspace/python/vision_seed/core/language_manager.py)：平台与游戏文案入口
- [core/data_manager.py](/C:/workspace/python/vision_seed/core/data_manager.py)：训练记录持久化
- [core/license_manager.py](/C:/workspace/python/vision_seed/core/license_manager.py)：本地授权逻辑

### 全局场景

- [scenes/menu_scene.py](/C:/workspace/python/vision_seed/scenes/menu_scene.py)
- [scenes/category_scene.py](/C:/workspace/python/vision_seed/scenes/category_scene.py)
- [scenes/game_host_scene.py](/C:/workspace/python/vision_seed/scenes/game_host_scene.py)
- [scenes/system_settings_scene.py](/C:/workspace/python/vision_seed/scenes/system_settings_scene.py)
- [scenes/license_scene.py](/C:/workspace/python/vision_seed/scenes/license_scene.py)
- [scenes/onboarding_scene.py](/C:/workspace/python/vision_seed/scenes/onboarding_scene.py)

`scenes/` 只放平台级页面，游戏私有页面放在 `games/<category>/<game>/scenes/`。

### 游戏层

每个游戏遵循当前项目约定结构：

```text
games/<category>/<game>/
├─ game.py
├─ i18n.py
├─ scenes/
├─ services/
└─ assets/
```

接入协议见 [core/game_contract.py](/C:/workspace/python/vision_seed/core/game_contract.py)。

### 公共训练运行时

[games/common/training_runtime](/C:/workspace/python/vision_seed/games/common/training_runtime) 提供通用 session、scoring、feedback、widgets 等能力。  
它当前是“公共运行时能力层”，不是要求所有游戏强制套同一个外壳。

## UI 现状

最近一轮 UI 收口已完成这些点：

- 平台页键盘优先交互补齐，分类页与系统设置页支持方向键焦点和 `Enter/Space`
- 主菜单不再每帧重建布局
- 平台页长文本增加换行和截断兜底
- `pong`、`depth_grab`、`precision_aim`、`weak_eye_key`、`eye_find_patterns` 已统一到一套更接近的 HUD 和结果页语法
- 公共文本与 HUD helper 已下沉到 [core/base_scene.py](/C:/workspace/python/vision_seed/core/base_scene.py)

仍值得继续观察的区域：

- 更复杂自定义页在小分辨率下的密度
- 红蓝模式下的人工试玩体验
- 非 runtime 自定义场景的进一步收口

## 测试

推荐命令：

```bash
python -m unittest discover -s tests -p "test_*.py"
python tests/run_ui_tests.py
```

对单个模块迭代时，先跑定向测试，再跑全量回归。

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

授权生成工具示例：

```bash
python tools/generate_license_token.py --license-id LIC_20260228_0001 --order-ref ORDER_001 --device-hash sha256:xxxxxxxx
```

## 文档说明

[docs/视觉训练小游戏分类指南.md](/C:/workspace/python/vision_seed/docs/视觉训练小游戏分类指南.md) 现在应主要作为“分类与设计约束文档”使用。  
如果实现状态发生变化，优先以代码和注册表为准，并同步更新文档，避免规划文本与实际接入状态脱节。
