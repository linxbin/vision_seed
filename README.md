# VisionSeed

VisionSeed 是一个基于 Python + Pygame 的多游戏视觉训练平台，而不是单一小游戏项目。

项目当前稳定保留六个顶层训练分类：

- `accommodation`
- `simultaneous`
- `fusion`
- `suppression`
- `stereopsis`
- `amblyopia`

## 当前内置游戏

当前代码库已接入 `18` 个内置训练游戏，注册入口见 [core/game_registry.py](/C:/workspace/python/vision_seed/core/game_registry.py)。

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
- `stereopsis.pop_nearest`
- `amblyopia.precision_aim`
- `amblyopia.whack_a_mole`
- `amblyopia.fruit_slice`

## 训练模式说明

当前项目中的红蓝眼镜训练分类为：

- `simultaneous`
- `fusion`
- `suppression`
- `stereopsis`

这些分类统一使用红蓝模式，并支持：

- `left_red_right_blue`
- `left_blue_right_red`

红蓝模式统一遵循项目内的减色融合规范：

- 背景使用纯品红 `RGB(255, 0, 255)`
- 左右视图反向平移后分别保留红 / 蓝单通道
- 重叠区域通过像素位运算变为纯黑
- 平移产生的边缘异常区域裁剪后再显示

以下分类保留普通模式训练：

- `accommodation`
- `amblyopia`

## 项目结构

平台基础设施位于：

- [core/](/C:/workspace/python/vision_seed/core)

全局页面位于：

- [scenes/](/C:/workspace/python/vision_seed/scenes)

各游戏模块位于：

- [games/](/C:/workspace/python/vision_seed/games)

测试位于：

- [tests/](/C:/workspace/python/vision_seed/tests)

推荐参考的关键文件：

- [main.py](/C:/workspace/python/vision_seed/main.py)
- [core/game_contract.py](/C:/workspace/python/vision_seed/core/game_contract.py)
- [core/game_registry.py](/C:/workspace/python/vision_seed/core/game_registry.py)
- [core/scene_manager.py](/C:/workspace/python/vision_seed/core/scene_manager.py)
- [core/language_manager.py](/C:/workspace/python/vision_seed/core/language_manager.py)
- [core/data_manager.py](/C:/workspace/python/vision_seed/core/data_manager.py)
- [scenes/game_host_scene.py](/C:/workspace/python/vision_seed/scenes/game_host_scene.py)

标准游戏目录结构：

```text
games/<category>/<game>/
├─ game.py
├─ i18n.py
├─ scenes/
├─ services/
└─ assets/
```

## 运行与测试

推荐环境：

- Python 3.10+
- Windows 10/11

安装依赖并启动：

```bash
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
python main.py
```

回归测试命令：

```bash
python -m unittest discover -s tests -p "test_*.py"
python tests/run_ui_tests.py
```

## 打包

打包说明见：

- [Packaging_README.md](/C:/workspace/python/vision_seed/Packaging_README.md)
- [package_secure.bat](/C:/workspace/python/vision_seed/package_secure.bat)
- [visionseed.spec](/C:/workspace/python/vision_seed/visionseed.spec)

## 文档

当前项目只保留 `README.md` 作为主文档入口。

如果实现状态发生变化，应优先同步注册表、测试和本文件，避免说明与代码状态脱节。

本文件负责记录：

- 当前分类与已接入游戏
- 当前项目结构与运行方式
- 与实现直接相关的稳定基线信息
