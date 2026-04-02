# Light Transfer Skill (黄石版)

> 基于原始版工作的实践固化 | 适用于 Windows PowerShell 环境

## 📖 概述

本版本基于 2026-04-02 晚间在黄石环境下的实际工作流程固化，记录了原始版技能在 Windows 上的**实际调用方式**和**注意事项**。

**工作流 ID**: `2037342126949797890`  
**API Key 来源**: 环境变量 `RUNNINGHUB_API_KEY`  
**命令行风格**: 直接运行脚本 `python scripts/light_transfer_cli.py`（而非 `-m` 模块方式）

---

## 🚀 快速开始（黄石环境）

### 1. 前置条件

- **Python**: 3.10+（验证可用：`python --version`）
- **依赖**: `pyyaml`, `requests`（可通过 `pip install -r requirements.txt` 安装）
- **网络**: 可访问 RunningHub API (`https://www.runninghub.cn`)

### 2. Python 调用方式

```cmd
REM 设置 API Key（当前会话有效）
set RUNNINGHUB_API_KEY=你的密钥

REM 进入技能目录
cd F:\u-claw\portable\app\core\node_modules\openclaw\skills\light-transfer-skill-huangshi

REM 1) 扫描生成组合（dry-run）
python scripts/light_transfer_cli.py --dry-run

REM 2) 正式运行
python scripts/light_transfer_cli.py

REM 3) 需要时续传
python scripts/light_transfer_cli.py --resume
```

**重要**：使用 `python scripts/light_transfer_cli.py` 而非 `python -m light-transfer-skill`，后者在 Windows 上可能因包名含连字符而失败。

### 3. 日志记录（推荐）

```cmd
set RUNNINGHUB_API_KEY=你的密钥
cd F:\u-claw\portable\app\core\node_modules\openclaw\skills\light-transfer-skill-huangshi
python scripts/light_transfer_cli.py 2>&1 | Tee-Object -FilePath "F:\光线迁移\run_YYYYMMDD_HHMM.log"
```

`Tee-Object` 是 PowerShell 命令，可同时显示并保存日志。使用 `cmd` 时可改用 `script.py > log.txt 2>&1`。

---

## ⚠️ 已知问题与对策

### 1. 扫描去重失败（Windows 大小写不敏感）

**现象**：`pic1` 和 `pic2` 目录中，每个文件会被列出两次（`1.jpg` 和 `1.JPG` 被视为不同），导致生成的 `combinations.json` 包含大量重复组合。

**原因**：`scanner.py` 中的 `Path.glob("*{ext}")` 在 Windows 上会同时匹配大小写变体，且未去重。

**影响**：处理时间成倍增加，但最终输出文件会覆盖（相同文件名）。

**对策**：
- 手动清理 `logs/combinations.json`，移除重复条目
- 或使用外部工具去重：`python -c "import json; data=json.load(open('logs/combinations.json')); uniq=list(set(tuple(d.items()) for d in data)); json.dump([dict(u) for u in uniq], open('logs/combinations.json','w'), indent=2)"`
- 或等待升级版本（东风版已修复）

### 2. PowerShell 语法陷阱

在 PowerShell 中设置环境变量时，应使用：

```powershell
$env:RUNNINGHUB_API_KEY='your_key'
```

而非 `set` 或 `export`。

在 `cmd.exe` 中使用：

```cmd
set RUNNINGHUB_API_KEY=your_key
```

---

## 📂 与东风版对比

| 特性 | 黄石版 (本版) | 东风版 |
|------|--------------|--------|
| 调用方式 | `python scripts/light_transfer_cli.py` | 相同 |
| UTF-8 编码修复 | ❌ 未修复 | ✅ 已修复 |
| 扫描去重 | ❌ 存在重复 | ✅ 已去重 |
| 适用场景 | 原始复现、调试 | 推荐日常使用 |
| 稳定性 | 一般（Windows 下可能编码错误） | 高 |

---

## 🛠️ 故障排除

### 错误: "RUNNINGHUB_API_KEY environment variable not set"
确保已设置环境变量，使用 `echo %RUNNINGHUB_API_KEY%` (cmd) 或 `$env:RUNNINGHUB_API_KEY` (PowerShell) 验证。

### 任务失败（805 错误）
检查 Workflow ID 是否正确，API Key 是否有权限。可登录 RunningHub 控制台验证。

### 扫描结果重复
见上文对策。

---

## 📝 本次工作参数

- **日期**: 2026-04-02
- **环境**: Windows 10/11, Python 3.12.10
- **运行时长**: 1 小时 21 分钟 19 秒
- **总任务数**: 72（含重复）
- **唯一组合**: 18（6 基图 × 3 光效）
- **结果**: 全部成功

---

## 🔄 版本历史

- **2026-04-02 v1.0.0-huangshi**: 基于原始版实践固化，记录 Windows 调用细节和注意事项。

---

**注意**：本版本为**历史工作流固化**，仅用于复现和参考。日常推荐使用东风版（已修复编码和去重问题）。
