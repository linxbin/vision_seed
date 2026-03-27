---
name: pygame-qa-and-bugfix
description: 诊断、修复并验证 VisionSeed 中的平台问题和具体训练游戏问题。适用于输入异常、路由错误、语言切换问题、HUD 遮挡、倒计时异常、GameHostScene 挂载问题、训练记录与 game_id 命名空间错误，以及需要做回归验证的 Python + Pygame 缺陷。
---

# 目标

用最小改动定位、修复并验证 VisionSeed 问题。

# 先判断归属

- 平台问题：`core/` 或全局 `scenes/`
- 游戏问题：优先在 `games/<category>/<game>/` 下修
- 不把单个游戏补丁塞进公共层

# 默认排查顺序

1. 输入与事件消费
2. `SceneManager`、`GameHostScene`、游戏根场景路由
3. HUD 布局、倒计时、遮挡
4. `LanguageManager` 与中英文显示
5. `game_id` 记录、历史、自适应范围
6. 游戏 `services/` 中的计分、会话、题目生成
7. 字体、音效、资源加载和回退

# 修复原则

- 优先局部修复
- 不无故扩大改动面
- 如必须重构，要说明是为修正边界或路由
- 修完同步更新测试

# 最少验证

- `python -m unittest discover -s tests -p "test_*.py"`
- UI/交互问题再跑 `python tests/run_ui_tests.py`
- 涉及入口或导入路径时做 `import main` 检查

# 输出

- 问题
- 原因
- 修复内容
- 验证结果
- 剩余风险
