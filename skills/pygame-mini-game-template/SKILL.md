---
name: pygame-mini-game-template
description: 为 VisionSeed 创建新的训练游戏模块模板。适用于在调节训练、同时视训练、融合视训练、脱抑制训练、立体视训练、弱视训练等分类下新增游戏，并生成符合 GameDescriptor、games 目录、i18n、services 和根场景路由的标准结构。
---

# 目标

快速创建一个能接入 VisionSeed 的新训练游戏，而不是生成通用小游戏样板。

# 默认输出

```text
games/<category>/<game>/
  game.py
  i18n.py
  scenes/
    root_scene.py
  services/
```

# 必守规则

- `game.py` 提供可注册到 `GameRegistry` 的 `GameDescriptor`
- `create_scene(manager)` 返回入口场景或 `root_scene`
- 游戏私有文案放 `i18n.py`
- 游戏逻辑、计分、记录、会话优先放 `services/`
- 不默认生成 `logic.py / renderer.py / constants.py`

# 最小可运行要求

- 可从分类菜单进入
- 有完整最小玩法闭环
- 有明确返回链路
- 有 `zh-CN` 和 `en-US` 文案
- 记录按 `game_id` 独立处理

# 默认顺序

1. 定义 `game_id`、分类、名称 key
2. 建 `game.py + i18n.py + scenes/ + services/`
3. 先做最小可运行流程
4. 再补帮助页、结算页、历史页或配置页
5. 最后补测试和 README
