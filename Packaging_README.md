# VisionSeed 打包与发布指南

## 概述

本文档说明如何将 VisionSeed 打包为 Windows 可分发版本，并确保运行时数据与用户隐私不随安装包分发。

当前基线版本：`v1.0.0`

## 打包前检查

1. 确认测试通过：

```cmd
python -m unittest discover -s tests -p "test_*.py"
```

2. 确认仓库干净：

```cmd
git status
```

3. 确认资产文件齐全：
- `assets/correct.wav`
- `assets/wrong.wav`
- `assets/completed.wav`
- `assets/SimHei.ttf`

## 难度等级（当前版本）

VisionSeed 当前为 **10 级难度**：

| 等级 | E字尺寸(px) |
|------|-------------|
| 1    | 5           |
| 2    | 10          |
| 3    | 20          |
| 4    | 30          |
| 5    | 40          |
| 6    | 50          |
| 7    | 60          |
| 8    | 70          |
| 9    | 80          |
| 10   | 85          |

## 打包方式

### 方式一：安全脚本（推荐）

```cmd
package_secure.bat
```

适合正式发布，流程更稳妥。

### 方式二：直接执行 spec

```cmd
pyinstaller visionseed.spec
```

## 产物结构

```text
项目根目录/
├── dist/
│   └── VisionSeed/
│       ├── VisionSeed.exe
│       ├── assets/
│       └── config/
└── build/
```

说明：
- `build/` 为中间产物，可删除
- 运行时用户数据不会写回仓库目录

## 运行时数据位置

程序运行后在用户目录生成数据：

- `%LOCALAPPDATA%/VisionSeed/data/records.json`
- `%LOCALAPPDATA%/VisionSeed/config/user_preferences.json`
- `%LOCALAPPDATA%/VisionSeed/license/license.json`

这三个文件不应随安装包分发。

## 隐私与安全要点

- 训练记录属于用户本地数据，不包含在仓库分发内容中
- 每个新用户首次运行时会初始化自己的本地配置和记录
- 建议发布前对产物做基础安全扫描（杀软/EDR）
- 建议对 `VisionSeed.exe` 做代码签名，减少系统拦截风险

## 常见问题

1. 打包失败（缺依赖）

```text
先执行 pip install -r requirements.txt
```

2. 运行时报 VC 运行库缺失

```text
安装 Visual C++ Redistributable:
https://aka.ms/vs/17/release/vc_redist.x64.exe
```

3. 没有声音

```text
检查系统音频设备；若启动时音频初始化失败，程序会自动降级静音运行。
```

4. 中文显示异常

```text
确认 assets/SimHei.ttf 在发布目录中存在。
```

## 发布建议（GitHub）

1. 推送主分支：`git push origin main`
2. 打版本标签：`git tag -a v1.0.0 -m "VisionSeed v1.0.0"` 后 `git push origin v1.0.0`
3. 在 GitHub Release 页面发布版本说明

---
最后更新：2026-02-28
