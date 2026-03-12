# VisionSeed Skills 说明

这组 Skills 用于辅助使用 Codex / ChatGPT 开发当前仓库的 VisionSeed 项目。

VisionSeed 不是通用的“经典小游戏合集”，而是一个基于 Python + Pygame 的多游戏视觉训练应用。当前仓库的真实结构是：

- 平台层：`core/`
- 全局公共页面：`scenes/`
- 游戏模块：`games/<category>/<game>/`
- 测试：`tests/core/`、`tests/scenes/`、`tests/games/`

## Skills 列表

当前包含以下 4 个 Skills：

1. `pygame-architecture`
2. `pygame-mini-game-template`
3. `pygame-ui-style-guide`
4. `pygame-qa-and-bugfix`

## 一、pygame-architecture

### 作用
用于约束 VisionSeed 的平台层、公共页面层和游戏模块层的架构边界。

### 适用场景
- 规划或重构项目目录结构
- 新增分类或新游戏接入
- 调整 `GameRegistry` / `GameHostScene` / `SceneManager`
- 抽离全局能力到 `core/`
- 收紧“公共页面”和“游戏私有页面”的边界

### 主要约束
- `scenes/` 只放全局公共页面
- 游戏私有页面必须放在 `games/<category>/<game>/scenes/`
- 公共基础设施放在 `core/`，不要写到 `shared/`
- 新游戏通过 `game.py` 暴露 `GameDescriptor`
- 训练记录、配置和文案优先按 `game_id` 命名空间隔离

## 二、pygame-mini-game-template

### 作用
用于在 VisionSeed 中快速创建一个新训练游戏模块。

### 适用场景
- 在 6 大训练分类下新增一个游戏
- 创建占位游戏或最小可运行原型
- 为新游戏搭好 `game.py / scenes / services / i18n.py` 骨架

### 默认输出结构

```text
games/<category>/<game>/
  game.py
  i18n.py
  scenes/
  services/
```

### 模板要求
- `game.py` 返回 `GameDescriptor`
- 多页面游戏优先使用 `scenes/root_scene.py`
- 游戏私有文案放 `i18n.py`
- 游戏规则、记录、会话逻辑优先抽到 `services/`
- 新游戏必须能通过 `GameRegistry` 接入分类菜单

## 三、pygame-ui-style-guide

### 作用
用于统一 VisionSeed 的全局页面、游戏页面和训练界面的 UI / UX 风格。

### 适用场景
- 主菜单、分类页、系统设置
- 游戏内菜单、训练页、帮助页、报告页、历史页
- HUD、按钮、面板、弹窗、倒计时、提示反馈

### 主要约束
- 尊重当前项目的窗口和布局约束，不要硬编码新的固定分辨率体系
- 中文和英文都必须可显示，避免字符方框
- 返回链路明确，所有菜单页应有返回入口
- 儿童向训练界面优先可读性、稳定性和柔和反馈

## 四、pygame-qa-and-bugfix

### 作用
用于诊断、修复并回归验证 VisionSeed 中的平台问题和具体游戏问题。

### 适用场景
- 输入、路由、倒计时、音效、语言切换问题
- `GameHostScene`、游戏根场景、游戏内菜单返回链路异常
- 训练记录、`game_id` 命名空间、自适应逻辑问题
- 某个具体游戏的玩法 bug 和页面 bug

### 主要约束
- 问题属于单个游戏时，优先在对应 `games/<category>/<game>/` 下修复
- 只有真正共享的问题才改 `core/` 或全局 `scenes/`
- 修复后至少跑对应测试和一次相关回归

## 使用建议

### 做结构调整时
优先使用：
- `pygame-architecture`

### 新增游戏时
优先使用：
- `pygame-mini-game-template`
- `pygame-ui-style-guide`

### 修页面或玩法问题时
优先使用：
- `pygame-qa-and-bugfix`

### 持续迭代时
4 个 Skills 可以配合使用：
- 架构 Skill 管平台与游戏边界
- 模板 Skill 管新游戏接入
- UI Skill 管界面一致性与儿童向可读性
- QA Skill 管修复与回归验证

## 说明

这些 Skills 不是 VisionSeed 运行时依赖，而是提供给 Codex / ChatGPT 的开发约束和工作流说明。
