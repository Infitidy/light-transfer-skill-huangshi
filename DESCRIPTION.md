# Light Transfer Skill (Huangshi Edition)

> 原始版工作流固化 - 基于 2026-04-02 黄石环境实践 | 适合 Windows 11 U 盘 OpenClaw

## 特点

- 📝 **真实记录**：完整记录原始版在 Windows 上的实际调用方式
- ⚡ **直接脚本**：使用 `python scripts/light_transfer_cli.py` 避免模块加载问题
- 🔧 **故障对策**：包含扫描重复问题的诊断和解决方法
- 💾 **日志模式**：PowerShell `Tee-Object` 实时保存运行日志

## 使用场景

- 需要复现原始版行为
- 兼容旧有流程和配置
- 学习原始工作流机制

## 快速开始

```powershell
# 设置 API Key
$env:RUNNINGHUB_API_KEY="your_key"

# 进入技能目录
cd F:\u-claw\portable\app\core\node_modules\openclaw\skills\light-transfer-skill-huangshi

# 扫描（注意：可能产生重复组合）
python scripts/light_transfer_cli.py --dry-run

# 正式运行
python scripts/light_transfer_cli.py 2>&1 | Tee-Object -FilePath "F:\光线迁移\run_20260402.log"
```

## 注意事项

- 本版保留原始扫描逻辑，在 Windows 上可能产生重复组合（每个文件被识别两次）
- 建议处理前手动去重 `logs/combinations.json`
- 如需更稳定体验，请使用东风版 (light-transfer-dongfeng)

## 文档

详细说明请见 [README_HUANGSHI.md](README_HUANGSHI.md)

## 许可

MIT © 2026 Claw助手
