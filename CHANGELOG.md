# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0-huangshi] - 2026-04-02

### Added
- 基于 2026-04-02 黄石环境实际工作流固化
- 记录 Windows PowerShell 下的调用方式：`python scripts/light_transfer_cli.py`
- 日志记录模式：`2>&1 | Tee-Object -FilePath`
- 故障排除章节：扫描去重失败的手动解决
- 实践参数：72 任务，1h21m 运行时长

### Notes
- 本版本保留原始扫描逻辑，可能产生重复组合
- 适用于需要复现原始行为的场景
- 推荐新用户使用东风版

## [1.0.0] - Original

- 基础功能：扫描、组合、调用 RunningHub API、下载输出
- 支持断点续传、模拟模式、日志记录
