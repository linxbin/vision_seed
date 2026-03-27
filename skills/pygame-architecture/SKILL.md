---
name: pygame-architecture
description: 为 VisionSeed 项目定义并约束多游戏视觉训练架构。适用于构建、重构或扩展包含 core、全局 scenes、games 模块、GameRegistry、GameHostScene、多语言、训练记录与 game_id 命名空间的 Python + Pygame 项目。
---

# 目标

按当前 VisionSeed 真实结构工作，不把代码重新带回 `launcher/`、`shared/` 或通用小游戏合集模式。

# 默认结构

```text
core/      # 平台能力
scenes/    # 全局公共页面
games/     # 游戏模块
tests/     # core/scenes/games 分层测试
```

游戏目录默认采用：

```text
games/<category>/<game>/
  game.py
  i18n.py
  scenes/
  services/
```

# 必守规则

- `core/` 只放公共基础设施
- `scenes/` 只放全局页面，不放游戏私有页面
- 游戏私有页面放 `games/<category>/<game>/scenes/`
- 游戏私有文案放 `i18n.py`
- 游戏规则、记录、会话优先放 `services/`
- 不新增 `shared/`、`launcher/` 作为主结构

# 接入规则

新游戏通过 `game.py` 暴露 `GameDescriptor`，至少包含：

- `game_id`
- `category`
- `name_key`
- `create_scene(manager)`

多页面游戏优先返回 `root_scene.py`，由 `GameHostScene` 挂载。

# 数据与文案

- 记录、配置、会话优先按 `game_id` 隔离
- 全局文案放 `core/language_manager.py`
- 游戏私有文案放各游戏 `i18n.py`
- 新增界面同时检查 `zh-CN` 和 `en-US`

# 默认工作流

1. 先保持现有用户流程不变
2. 再收紧平台层和游戏层边界
3. 再下沉游戏私有逻辑到 `services/`
4. 最后补测试和文档
