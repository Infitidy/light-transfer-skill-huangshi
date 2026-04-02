---
name: light-transfer-skill-huangshi
description: Light Transfer Skill (Huangshi Edition) - Original workflow with Windows PowerShell usage notes. Scans two image directories, generates all combinations, processes each with the RunningHub workflow, and saves outputs. This edition documents the actual command-line usage on Windows (direct script call) and includes workarounds for scanner duplication.
version: 1.0.0-huangshi
author: Claw助手
license: MIT
repository: https://github.com/Infitidy/light-transfer-skill
---

# Light Transfer Skill (黄石版)

基于 2026-04-02 黄石环境实际工作流固化的图片光线迁移工具。

## 核心特性

- 使用 `python scripts/light_transfer_cli.py` 直接运行（避免 `-m` 模块加载问题）
- 通过环境变量 `RUNNINGHUB_API_KEY` 提供 API Key
- 完整记录日志到文件（PowerShell `Tee-Object`）
- 保持原始版逻辑，包含扫描去重问题（已记录对策）

## 使用方式

见 `README_HUANGSHI.md`。

## 配置

同原始版，`config.yaml` 可自定义路径、工作流 ID、处理参数等。

## 安装位置

```
.openclaw/
  skills/
    light-transfer-skill-huangshi/
      scripts/
        light_transfer_cli.py
        runner.py
        scanner.py
        ...
      config.yaml
      README_HUANGSHI.md
      SKILL.md
```

## 与东风版的区别

东风版已修复 Windows 编码和扫描去重问题，建议新用户使用东风版。黄石版用于保持原始行为一致性。
