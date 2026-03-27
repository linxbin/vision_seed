# VisionSeed v2.1.0

VisionSeed v2.1.0 在 v2.0.0 的多游戏平台基础上，继续补齐融合训练内容、稳定性修复和发布细节，重点完善了 `fusion.tangram_fusion` 与若干训练游戏的可用性。

## Highlights

- 新增 `fusion.tangram_fusion`，提供红蓝眼镜下的融合七巧板缺块识别训练
- 修复 `amblyopia.fruit_slice` 的炸弹死局，确保每轮始终存在可选水果目标
- 打包流程补齐游戏资源文件纳入，减少发布包缺素材问题
- 补强 `tangram_fusion` 中文文案与训练页细节，提升可读性与可用性

## Added

- 新增内置游戏 `fusion.tangram_fusion`
- 新增融合七巧板相关场景、服务层与测试覆盖
- 新增 `tangram_fusion` 专项 i18n 回归测试

## Improved

- 优化融合七巧板训练页缺口提示，仅保留线框提示，减少视觉干扰
- 下移训练页底部操作提示，避免与候选拼块重叠
- 完善发布文档中的基线版本与标签示例

## Fixed

- 修复融合七巧板中文文案乱码问题
- 修复切水果游戏出现仅炸弹回合导致无法正确作答的问题
- 修复打包产物缺少部分游戏资源的问题

## Verification

- `python -m unittest discover -s tests -p "test_*.py"`
- `python tests/run_ui_tests.py`

本次发布目标产物：

- `shiya-v2.1.0-windows-x64.zip`
