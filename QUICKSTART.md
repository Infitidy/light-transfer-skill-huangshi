# Light Transfer Skill - 快速开始

## 📦 1. 准备图片目录

```bash
mkdir -p ~/光线迁移/pic1   # 主体图片（人物、景物）
mkdir -p ~/光线迁移/pic2   # 光源/光效图片

# 复制图片到对应目录
# 例如:
# pic1/阿霞.jpg, pic1/张宁1.jpg
# pic2/暖光斑1.jpg, pic2/百叶窗.jpg
```

## 📝 2. 配置

在 skill 目录内（`~/.npm-global/lib/node_modules/openclaw/skills/light-transfer-skill/`）:

```bash
# 复制配置模板
cp references/config.example.yaml config.yaml

# 按需修改路径（如果使用默认位置 /home/lee/光线迁移/pic1 则无需修改）
```

## 🔑 3. 配置 API Key（必做）

### 方法 A: 环境变量（推荐）
```bash
export RUNNINGHUB_API_KEY="你的_RunningHub_API_Key"
```

### 方法 B: OpenClaw 配置文件
编辑 `~/.openclaw/openclaw.json`:

```json
{
  "skills": {
    "entries": {
      "runninghub": {
        "apiKey": "你的_RunningHub_API_Key"
      }
    }
  }
}
```

### 方法 C: 命令行参数
```bash
python3 scripts/light_transfer_cli.py --api-key 你的_RunningHub_API_Key
```

### 如何获取 API Key？
1. 访问 https://www.runninghub.cn
2. 登录后进入 💼 **"企业API"** 或 **"API管理"**
3. 创建新 Key 或复制已有 Key
4. 复制保存（只显示一次）

## 🧪 4. 测试

```bash
# 预览组合（不实际运行）
python3 scripts/light_transfer_cli.py --dry-run

# 模拟运行（测试流程，不消耗 API 额度）
python3 scripts/light_transfer_cli.py --simulate
```

## 🚀 5. 正式运行

```bash
# 首次运行
python3 scripts/light_transfer_cli.py

# 如果中断，下次用 resume 续传
python3 scripts/light_transfer_cli.py --resume
```

## 📂 6. 查看结果

输出文件位于:
```
outputs/2026-04-01/阿霞_暖光斑1.png
outputs/2026-04-01/report.json   # 运行报告
```

日志和进度:
```
logs/light_transfer.log
logs/completed.json   # 已完成的组合
logs/failed.json      # 失败的记录
```

---

## ⚡ 单条命令快速启动

```bash
# 在 skill 目录下
export RUNNINGHUB_API_KEY="xxx" && python3 scripts/light_transfer_cli.py
```

---

**问题?** 查看完整文档: `README.md`
