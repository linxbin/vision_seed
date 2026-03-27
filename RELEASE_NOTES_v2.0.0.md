# VisionSeed v2.0.0

VisionSeed v2.0.0 从单一训练流程升级为多游戏视觉训练平台，统一了平台层架构、训练运行时、分类导航与发布流程。

## Highlights

- 新增六大稳定训练分类：`accommodation`、`simultaneous`、`fusion`、`suppression`、`stereopsis`、`amblyopia`
- 内置训练游戏扩展到 18 个，统一通过 `core/game_registry.py` 注册
- 引入多游戏宿主与路由结构，平台场景与游戏私有场景边界更清晰
- 统一红蓝眼镜训练模式与减色融合规则，覆盖同时视、融合视、脱抑制、立体视训练
- 补齐大规模单元测试与 UI 回归测试，发布前回归通过

## Added

- 新增多款训练游戏，包括 `catch_fruit`、`snake`、`pong`、`push_box`、`tetris`、`path_fusion`、`find_same`、`red_blue_catch`、`depth_grab`、`ring_flight`、`pop_nearest`、`precision_aim`、`whack_a_mole`、`fruit_slice`
- 新增 `games/common/training_runtime` 统一训练运行时
- 新增 `games/common/anaglyph.py` 统一红蓝合成能力
- 新增分类页、系统设置页、游戏宿主页与推荐逻辑
- 新增品牌图标、打包资源与技能文档

## Improved

- E 方向训练已完整迁入游戏模块，避免旧 `scenes/` 兼容壳继续膨胀
- 菜单、引导、授权、分类和 HUD 布局统一到平台化视觉风格
- 全屏、窗口最小尺寸、底部文案遮挡和多处红蓝训练交互表现已优化
- 打包脚本支持按 git tag 生成版本化 zip 包

## Fixed

- 修复多个训练游戏在全屏、滤镜方向、布局遮挡、交互反馈与文案上的问题
- 修复 i18n 覆盖不足、指标标签缺失、训练结果与推荐信息展示问题
- 修复部分历史记录、数据 schema 与测试覆盖空缺问题

## Verification

- `python -m unittest discover -s tests -p "test_*.py"`
- `python tests/run_ui_tests.py`

本次发布包含 Windows x64 打包产物：

- `shiya-v2.0.0-windows-x64.zip`
