# E Orientation Training

## Overview

E方向训练游戏，包含游戏内菜单、配置、训练、报告、历史五个页面，并通过 `scenes/root_scene.py` 管理内部路由。

## Structure

- `game.py`: 游戏入口与 descriptor
- `i18n.py`: 游戏私有文案
- `scenes/`: 菜单、配置、训练、报告、历史、root scene
- `services/records_service.py`: 训练记录读写与 `game_id` 过滤

## Notes

- 记录命名空间固定为 `accommodation.e_orientation`
- 自适应评估默认只读取当前游戏记录
