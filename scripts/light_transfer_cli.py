#!/usr/bin/env python3
"""
Light Transfer Skill Entry Point

This script provides the main interface for the light-transfer skill.
It can be called directly or through the OpenClaw skill system.
"""

import sys
import os
from pathlib import Path

# Setup paths
SKILL_DIR = Path(__file__).parent.parent  # light-transfer-skill 根目录
SCRIPTS_DIR = SKILL_DIR / 'scripts'
sys.path.insert(0, str(SCRIPTS_DIR))

# Add OpenClaw_RH_Skills to path for RunningHub modules
# OpenClaw_RH_Skills 位于 skills/OpenClaw_RH_Skills (与 light-transfer-skill 同级)
SKILLS_ROOT = SKILL_DIR.parent  # skills/ 根目录
RH_SKILLS_DIR = SKILLS_ROOT / 'OpenClaw_RH_Skills' / 'runninghub' / 'scripts'
if RH_SKILLS_DIR.exists():
    sys.path.insert(0, str(RH_SKILLS_DIR))
else:
    print(f"Warning: OpenClaw_RH_Skills not found at {RH_SKILLS_DIR}")

# Import core modules
from runner import RunningHubRunner
from scanner import scan_images, generate_combinations, build_output_name, save_combinations
from utils import (
    setup_project_logging,
    load_config,
    ensure_dir,
    format_duration,
    calculate_eta,
    retry
)
import logging
import argparse
import time
import json
from datetime import datetime

logger = logging.getLogger("light-transfer")

# ============================================
# MockRunner for simulation mode
# ============================================
class MockRunner:
    """模拟 RunningHubRunner，用于测试流程"""
    def __init__(self, config: dict):
        self.config = config
        self.counter = 0
        self.output_dir = None

    def run_one(self, pic1_path: Path, pic2_path: Path, output_name: str) -> Path:
        self.counter += 1
        taskid = f"sim_{self.counter:06d}"
        logger.info(f"[模拟] 提交任务: {output_name} → {taskid}")
        time.sleep(0.5)

        output_dir = self.output_dir or Path(self.config['paths']['output_base']) / datetime.now().strftime("%Y-%m-%d")
        output_dir.mkdir(parents=True, exist_ok=True)
        output_path = output_dir / output_name
        output_path.write_text(f"Simulated output for task {taskid}\n")
        logger.info(f"[模拟] 文件已创建: {output_path}")
        return output_path

# ============================================
# Main Project Class
# ============================================
class LightTransferSkill:
    def __init__(self, config: dict, args: argparse.Namespace):
        self.config = config
        self.args = args
        self.start_time = time.time()

        # Paths
        self.output_dir = Path(args.output) if args.output else Path(config['paths']['output_base']) / datetime.now().strftime("%Y-%m-%d")
        self.log_dir = Path(config['paths']['log_dir'])
        self.combinations_file = self.log_dir / "combinations.json"
        self.completed_file = self.log_dir / "completed.json"
        self.failed_file = self.log_dir / "failed.json"

        ensure_dir(self.log_dir)
        ensure_dir(self.output_dir)

        self.runner = None
        self.combinations = []
        self.completed_before = set()
        self.completed = set()
        self.results = {"success": [], "failed": []}

    def load_combinations(self):
        if not self.combinations_file.exists():
            raise FileNotFoundError(
                f"组合列表不存在: {self.combinations_file}\n"
                "请先运行 scanner 生成组合:\n"
                "  python -m light-transfer-skill --dry-run"
            )
        with open(self.combinations_file, 'r', encoding='utf-8') as f:
            self.combinations = json.load(f)
        logger.info(f"加载组合列表: {len(self.combinations)} 个")

        # Apply output extension override
        ext = self.config['processing'].get('output_extension', 'png')
        for combo in self.combinations:
            old_name = combo['output_name']
            stem = Path(old_name).stem
            combo['output_name'] = f"{stem}.{ext}"

    def load_progress(self):
        self.completed_before = set()
        if self.args.resume and self.completed_file.exists():
            try:
                with open(self.completed_file, 'r', encoding='utf-8') as f:
                    loaded = set(json.load(f))
                self.completed_before = loaded
                self.completed = loaded.copy()
                logger.info(f"加载进度: 已跳过 {len(self.completed_before)} 个组合")
            except Exception as e:
                logger.warning(f"加载进度文件失败，将从头开始: {e}")
        self.completed = set(self.completed_before)

    def save_progress(self):
        with open(self.completed_file, 'w', encoding='utf-8') as f:
            json.dump(list(self.completed), f, indent=2, ensure_ascii=False)

    def save_failed(self):
        if self.results["failed"]:
            with open(self.failed_file, 'w', encoding='utf-8') as f:
                json.dump(self.results["failed"], f, indent=2, ensure_ascii=False)
            logger.info(f"失败清单已保存: {self.failed_file} ({len(self.results['failed'])} 条)")

    def save_report(self):
        total = len(self.combinations)
        success = len(self.results["success"])
        failed = len(self.results["failed"])
        elapsed = time.time() - self.start_time

        report = {
            "start_time": datetime.fromtimestamp(self.start_time).isoformat(),
            "end_time": datetime.now().isoformat(),
            "elapsed_seconds": elapsed,
            "total_combinations": total,
            "success_count": success,
            "failed_count": failed,
            "skip_count": len(self.completed_before),
            "success_rate": f"{(success/total*100):.1f}%" if total > 0 else "N/A",
            "output_directory": str(self.output_dir),
            "success_list": self.results["success"],
            "failed_list": self.results["failed"]
        }

        report_file = self.output_dir / "report.json"
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)

        logger.info("=" * 60)
        logger.info("[STAT] 运行报告")
        logger.info("=" * 60)
        logger.info(f"总组合数: {total}")
        logger.info(f"成功: {success}")
        logger.info(f"失败: {failed}")
        logger.info(f"跳过: {len(self.completed_before)}")
        logger.info(f"成功率: {report['success_rate']}")
        logger.info(f"总耗时: {format_duration(elapsed)}")
        logger.info(f"输出目录: {self.output_dir}")
        logger.info(f"详细报告: {report_file}")
        logger.info("=" * 60)

    def initialize_runner(self):
        if self.args.simulate:
            logger.info("🟢 模拟模式：使用 MockRunner")
            self.runner = MockRunner(self.config)
        else:
            from runner import RunningHubRunner
            self.runner = RunningHubRunner(self.config)
        self.runner.output_dir = self.output_dir

    def run_all(self):
        logger.info("=== 开始处理所有组合 ===")

        pending_combos = [
            combo for combo in self.combinations
            if f"{Path(combo['pic1']).name}|{Path(combo['pic2']).name}" not in self.completed
        ]

        total = len(pending_combos)
        logger.info(f"待处理: {total} 个组合")

        if total == 0:
            logger.info("[OK] 所有组合已处理完成")
            return

        for i, combo in enumerate(pending_combos, 1):
            pic1_path = Path(combo['pic1'])
            pic2_path = Path(combo['pic2'])
            output_name = combo['output_name']
            combo_key = f"{pic1_path.name}|{pic2_path.name}"

            logger.info(f"[{i}/{total}] 处理: {pic1_path.name} + {pic2_path.name} → {output_name}")

            try:
                output_path = self.runner.run_one(pic1_path, pic2_path, output_name)
                if output_path:
                    self.results["success"].append({"combo": combo_key, "output": str(output_path)})
                    self.completed.add(combo_key)
                    logger.info(f"[OK] 完成: {output_name}")
                else:
                    raise RuntimeError("runner 返回 None")
            except Exception as e:
                logger.error(f"[ERR] 失败: {combo_key} - {e}")
                self.results["failed"].append({"combo": combo_key, "error": str(e)})
                self.save_progress()

            if i % 5 == 0:
                elapsed = time.time() - self.start_time
                eta = calculate_eta(self.start_time, i, total)
                logger.info(f"进度: {i}/{total}, 剩余: {eta}")

            time.sleep(self.config['processing'].get('delay_between_tasks', 5))

        logger.info("=== 所有组合处理完成 ===")

    def run(self):
        try:
            self.initialize_runner()
            self.load_combinations()
            self.load_progress()
            self.run_all()
            self.save_progress()
            self.save_failed()
            self.save_report()
            return 0
        except KeyboardInterrupt:
            logger.warning("\n[WARN]  用户中断，正在保存进度...")
            self.save_progress()
            self.save_failed()
            return 130
        except Exception as e:
            logger.exception(f"[ERR] 技能执行失败: {e}")
            self.save_progress()
            self.save_failed()
            return 1

# ============================================
# CLI Entry Point
# ============================================
def main():
    parser = argparse.ArgumentParser(
        description="Light Transfer Skill - Automate image light transfer using RunningHub AI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 扫描组合（仅预览，不处理）
  python -m light-transfer-skill --dry-run

  # 正式运行
  python -m light-transfer-skill

  # 断点续传
  python -m light-transfer-skill --resume

  # 指定输出目录
  python -m light-transfer-skill --output outputs/custom_run

  # 模拟模式（测试流程）
  python -m light-transfer-skill --simulate

  # 调试日志
  python -m light-transfer-skill --log-level DEBUG
        """
    )

    parser.add_argument("--config", default="config.yaml", help="配置文件路径")
    parser.add_argument("--output", "-o", help="覆盖输出目录")
    parser.add_argument("--concurrent", type=int, default=1, help="并发数（默认1）")
    parser.add_argument("--resume", action="store_true", help="断点续传")
    parser.add_argument("--simulate", action="store_true", help="模拟模式")
    parser.add_argument("--dry-run", action="store_true", help="仅扫描，不执行处理")
    parser.add_argument("--log-level", default="INFO", choices=["DEBUG", "INFO", "WARNING", "ERROR"])

    args = parser.parse_args()

    # Setup logging
    setup_project_logging(level=args.log_level)
    global logger
    logger = logging.getLogger("light-transfer")

    if args.dry_run:
        logger.info("=== dry-run 模式：仅扫描 ===")
        try:
            import subprocess
            subprocess.run(
                [sys.executable, str(SKILL_DIR / 'scripts' / 'scanner.py'), "--config", args.config],
                check=True
            )
            logger.info("扫描完成，组合列表已生成")
            logger.info("运行 'python -m light-transfer-skill' 开始正式处理")
            return 0
        except subprocess.CalledProcessError as e:
            logger.error(f"扫描失败: {e}")
            return e.returncode

    # Load config
    try:
        config = load_config(args.config)
    except Exception as e:
        logger.error(f"配置加载失败: {e}")
        return 1

    # Run
    project = LightTransferSkill(config, args)
    return project.run()

if __name__ == "__main__":
    sys.exit(main())
