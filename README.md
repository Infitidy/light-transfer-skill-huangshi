# Light Transfer Skill

> 自动图片光线迁移工具 - 基于 RunningHub AI 应用

## 📖 概述

该技能自动扫描两个图片目录（主体 + 光源），生成所有组合，调用 RunningHub AI 应用进行光线迁移处理，并保存输出文件。

**工作流 ID**: `2037342126949797890`

## 🚀 快速开始

### 1. 安装技能
```bash
# 技能已安装在 OpenClaw 的 skills 目录
# 位置: ~/.npm-global/lib/node_modules/openclaw/skills/light-transfer-skill/
```

### 2. 准备图片目录
```bash
# 创建目录
mkdir -p ~/光线迁移/pic1   # 主体图片
mkdir -p ~/光线迁移/pic2   # 光源/光效图片

# 放入图片（支持 jpg, png, webp）
# 例如：
# pic1/阿霞.jpg, pic1/张宁1.jpg, pic1/张宁2.jpg
# pic2/暖光斑1.jpg, pic2/暖光斑2.jpg
```

### 3. 配置
复制示例配置：
```bash
cp references/config.example.yaml config.yaml
# 按需修改 pic1_dir, pic2_dir 等路径
```

### 4. 预览组合（不处理）
```bash
python -m light-transfer-skill --dry-run
```

### 5. 正式运行
```bash
python -m light-transfer-skill
```

## 📋 命令行接口

```bash
python -m light-transfer-skill [OPTIONS]
```

| 选项 | 说明 |
|------|------|
| `--config <path>` | 配置文件路径（默认: config.yaml） |
| `--output <dir>` | 覆盖输出目录 |
| `--concurrent <N>` | 并发数（默认: 1，建议保持1） |
| `--resume` | 断点续传（跳过已完成） |
| `--simulate` | 模拟模式（不调用 API，测试流程） |
| `--dry-run` | 仅扫描组合，不执行处理 |
| `--log-level <LEVEL>` | 日志级别（DEBUG/INFO/WARNING/ERROR） |
| `--api-key <KEY>` | 直接提供 API Key（优先级最高） |

## 📂 输出结构

```
光线迁移/
├── outputs/
│   └── 2026-04-01/
│       ├── 阿霞_暖光斑1.png
│       ├── 阿霞_暖光斑2.png
│       ├── 张宁1_暖光斑1.png
│       ├── report.json          # 运行报告
├── logs/
│   ├── combinations.json        # 组合列表
│   ├── completed.json           # 已完成记录
│   ├── failed.json              # 失败记录
│   └── light_transfer.log       # 详细日志
└── config.yaml                  # 你的配置
```

## 🔧 API Key 配置

RunningHub API 密钥是必需的。系统按优先级顺序查找：

```
1. 命令行参数: --api-key YOUR_KEY
2. 环境变量:   RUNNINGHUB_API_KEY
3. OpenClaw 配置文件: ~/.openclaw/openclaw.json → skills.entries.runninghub.apiKey
```

### 推荐方式：环境变量
```bash
export RUNNINGHUB_API_KEY="your_runninghub_api_key_here"
```

### 获取 API Key 步骤
1. 登录 RunningHub: https://www.runninghub.cn
2. 进入 "企业API" 或 "API管理" 页面
3. 创建新 API Key 或复制已有 Key
4. 妥善保存（密钥仅显示一次）

### 验证 API Key
```bash
# 测试连接和余额
python3 scripts/light_transfer_cli.py --check  # 或使用 runninghub.py 的 --check
```

**安全提示**:
- API Key 关联您的账户和计费，请勿泄露
- 建议使用后从 shell 历史中清除
- 不要将 API Key 硬编码到脚本中

## 🐛 故障排除

### 错误: "RUNNINGHUB_API_KEY environment variable not set"
**原因**: 未找到 API Key
**解决**: 通过上述任一方式提供 API Key

### 错误: "未找到运行器模块"
**原因**: 技能安装不完整
**解决**: 确保 `scripts/runner.py` 和 `scripts/runninghub*.py` 存在

### 组合列表不存在
**原因**: 未扫描生成
**解决**: 先运行 `python -m light-transfer-skill --dry-run`

### 任务失败（805 错误）
**原因**: 工作流 ID 不正确或权限不足
**解决**: 检查 `config.yaml` 中的 `workflow_id` 是否正确

## 📊 运行报告

完成后会在输出目录生成 `report.json`：
```json
{
  "total_combinations": 6,
  "success_count": 6,
  "failed_count": 0,
  "success_rate": "100.0%",
  "elapsed_seconds": 461,
  "output_directory": "outputs/2026-04-01"
}
```

## 🔄 断点续传

使用 `--resume` 可跳过已完成组合：
```bash
python -m light-transfer-skill --resume
```
进度保存在 `logs/completed.json`（自动管理）。

## 🧪 模拟模式

测试流程而不调用真实 API：
```bash
python -m light-transfer-skill --simulate
```
会创建空占位文件，用于验证目录结构和命名。

## 📝 技术细节

- **纯 API 方案**: 使用 `runninghub_app.py`，不依赖浏览器
- **智能轮询**: 三阶段（密集→稀疏→冲刺）
- **自动重试**: 上传失败自动重试（最多3次）
- **状态持久化**: 支持中断恢复

## 🔗 相关文档

- `SKILL.md` - 技能规范（系统自动读取）
- `scripts/runner.py` - RunningHub API 封装
- `scripts/scanner.py` - 目录扫描与组合
- `scripts/utils.py` - 工具函数
- `scripts/poll_task.py` - 轮询逻辑
- `references/config.example.yaml` - 配置示例

## 📄 License

MIT

---

**版本**: 1.0.0
**维护**: Claw助手
**最后更新**: 2026-04-01 (固化为 Skill)