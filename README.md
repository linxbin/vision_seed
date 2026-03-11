# VisionSeed (视芽)

VisionSeed 是一个基于 Python + Pygame 的 Windows 视觉训练应用。
项目围绕 E 字方向识别训练展开，包含授权、首次引导、配置、训练、报告和历史记录等完整场景。

## 当前实现功能

- 启动流程：先校验本地授权；已授权但未完成引导时进入首次引导，否则进入主菜单
- 训练内容：显示上/下/左/右方向的 E 字，使用方向键作答；相邻两题不会重复同一方向
- 难度系统：10 级，E 字尺寸范围为 `5px` 到 `85px`
- 配置页可调项：起始难度、题量、音效、语言、自适应难度
- 窗口能力：支持可调整窗口大小、全屏切换，并记住全屏偏好
- 题量范围：`0-1000`，支持 0 题边界；0 题时会直接生成报告
- 快捷训练模板：儿童 / 成人 / 恢复 三个模板，可一键应用后直接开训
- 训练反馈：答对/答错音效、粒子反馈、轻微屏幕震动、连击显示
- 暂停机制：`P` 键或按钮暂停/继续；窗口失焦时自动暂停
- 训练结束体验：播放完成音并平滑过渡到报告页，按 `Enter` 可跳过等待
- 报告页：入场淡入、结果卡片分段出现、数值滚动、与上一次训练的趋势对比、下一次训练建议、自适应调级结果
- 历史页：本地 JSON 持久化，支持日期筛选（全部 / 7天 / 30天）、难度筛选、按时间/正确率排序、分页查看
- 多语言：`en-US` / `zh-CN`，中文优先使用 `assets/SimHei.ttf`
- 启动健康检查：资源缺失或音频初始化失败时自动降级，不阻断启动
- 本地授权：设备绑定激活码校验，授权码前缀为 `VS1.`

## 与当前代码一致的说明

- README 中的“30 秒快速上手”是引导页标题，不是自动倒计时 30 秒后关闭的页面
- 典型场景流转为：授权 -> 引导 -> 菜单 -> 配置 / 训练 / 报告 / 历史，而不是固定的单一路径
- 报告页除了展示成绩，还会读取最近历史记录并给出趋势与下一次训练建议
- 全屏状态下按 `Esc` 会退出全屏；当前场景也可能继续处理这个按键

## 运行环境

- Python 3.10+（推荐 3.11+）
- Windows 10/11
- 依赖见 `requirements.txt`

当前运行依赖：

```txt
pygame==2.5.2
```

## 快速开始

```bash
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
python main.py
```

## 快捷键

- 主菜单：`1/2/3/4` 对应训练 / 配置 / 历史 / 退出；`5/6/7` 对应儿童 / 成人 / 恢复模板
- 训练：方向键作答，`P` 暂停/继续，`Esc` 返回菜单，结束过渡时 `Enter` 立即进入报告
- 配置：`Enter` 保存并开始训练，`Ctrl+S` 保存返回，`Esc` 取消，`M/L/A` 切换音效 / 语言 / 自适应，`↑/↓` 调整难度
- 历史：`←/→` 翻页，`R` 刷新，`Esc` 返回菜单
- 报告：`Enter` 再来一组，`Esc` 返回菜单
- 授权：`Enter` 激活，`C` 复制设备哈希，`Ctrl+V` 粘贴授权码，`Esc` 退出程序
- 全局窗口：`F11` 或 `Alt+Enter` 切换全屏；全屏时按 `Esc` 会退出全屏

## 运行测试

```bash
python -m unittest discover -s tests -p "test_*.py"
```

当前测试覆盖重点：

- 自适应难度逻辑
- 配置页状态与输入校验
- 训练计分、暂停、结束过渡、0 题边界
- 报告页动画与场景流转
- 历史记录筛选、排序、分页
- 授权激活与设备绑定校验
- 部分 Pygame UI 场景渲染与交互

## 项目结构

```text
├── assets/
│   ├── correct.wav
│   ├── wrong.wav
│   ├── completed.wav
│   └── SimHei.ttf
├── config/
│   ├── display.py
│   ├── game.py
│   ├── levels.py
│   └── user_preferences.example.json
├── core/
│   ├── adaptive_manager.py
│   ├── app_paths.py
│   ├── base_scene.py
│   ├── data_manager.py
│   ├── e_generator.py
│   ├── language_manager.py
│   ├── license_manager.py
│   ├── preferences_manager.py
│   ├── scene_manager.py
│   ├── sound_manager.py
│   └── startup_health.py
├── scenes/
│   ├── menu_scene.py
│   ├── license_scene.py
│   ├── onboarding_scene.py
│   ├── config_scene.py
│   ├── training_scene.py
│   ├── report_scene.py
│   └── history_scene.py
├── tests/
├── tools/
│   └── generate_license_token.py
├── Packaging_README.md
├── main.py
└── visionseed.spec
```

## 数据与文件位置

程序运行时默认写入以下用户目录：

- `%LOCALAPPDATA%/VisionSeed/data/records.json`
- `%LOCALAPPDATA%/VisionSeed/config/user_preferences.json`
- `%LOCALAPPDATA%/VisionSeed/license/license.json`

训练记录当前使用 `schema_version = 2`，主要字段包括：

- `timestamp`
- `session_id`
- `difficulty_level`
- `e_size_px`
- `total_questions`
- `correct_count`
- `wrong_count`
- `duration_seconds`
- `accuracy_rate`

兼容与迁移行为：

- 旧版 `data/records.json` 会迁移到用户目录
- 旧版 `config/user_preferences.json` 或 `data/user_preferences.json` 会迁移到用户目录
- 旧记录会在读取时做字段补齐和规范化

## 授权说明

- 启动时会检查本地授权文件；无授权或授权无效时进入授权页
- 授权与当前设备哈希绑定，不匹配的授权码会被拒绝
- 本地授权文件会保存激活时间、授权 ID 和脱敏后的订单尾号
- 卖家侧可用以下工具生成授权码：

```bash
python tools/generate_license_token.py --license-id LIC_20260228_0001 --order-ref ORDER_001 --device-hash sha256:xxxxxxxx
```

如需设置过期时间，可额外传入：

```bash
--expires-at 2026-12-31T23:59:59Z
```

## 打包发布

请参考 [Packaging_README.md](Packaging_README.md)。

当前仓库中的打包相关文件：

- `visionseed.spec`
- `package_secure.bat`
- `Packaging_README.md`

## 已知限制

- 当前 UI 测试以 headless 的 Pygame 场景测试为主，不是完整的端到端自动化回放
- 授权方案是本地最小可落地实现，适合离线校验，但不等同于强对抗安全方案
- 若 `assets/SimHei.ttf` 缺失，中文会回退到系统字体
- 当前主要面向 Windows 桌面环境

## 许可证

本项目仅供学习和非商业用途。
