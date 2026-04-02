# Contributing to Light Transfer Skill (Huangshi Edition)

感谢您考虑为此技能做贡献！

## 如何贡献

### 报告问题

如果您发现 bug 或有功能建议，请在 GitHub Issues 中提交，包括：

- 操作系统和 Python 版本
- 完整的错误信息（如有日志请附上）
- 复现步骤

### 代码贡献

1. Fork 本仓库
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 开启 Pull Request

### 开发环境

```bash
# 克隆仓库
git clone https://github.com/yourusername/light-transfer-skill-huangshi.git
cd light-transfer-skill-huangshi

# 安装依赖
pip install -r requirements.txt

# 运行测试（模拟模式）
python scripts/light_transfer_cli.py --simulate
```

### 代码风格

- 遵循 PEP 8 编码规范
- 添加必要的日志（使用 `logging` 模块）
- 保持向后兼容性

## 许可证

本项目采用 MIT 许可证，贡献即意味着您同意您的代码将在该许可证下发布。
