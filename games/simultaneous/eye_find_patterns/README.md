# Eye Find Patterns

## Overview

双眼找图案游戏，当前采用单游戏场景状态机，覆盖首页、帮助页、训练页、结算页。

## Structure

- `game.py`: 游戏入口与 descriptor
- `i18n.py`: 游戏私有文案
- `scenes/game_scene.py`: UI状态与交互编排
- `services/scoring_service.py`: 积分与连击规则
- `services/pattern_service.py`: 图案生成、左右位置、滤镜叠加
- `services/session_service.py`: 单局与单次倒计时会话管理

## Notes

- 游戏标识固定为 `simultaneous.eye_find_patterns`
- 当前尚未拆成 `root_scene + 多子场景`，后续可继续收敛
