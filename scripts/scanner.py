#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
图片扫描器 - 扫描 pic1 和 pic2 目录，生成所有配对组合
"""

import sys
import json
import logging
from pathlib import Path
from typing import List, Tuple

logger = logging.getLogger(__name__)

# 支持的图片格式
SUPPORTED_EXTENSIONS = {
    '.jpg', '.jpeg', '.png', '.webp',
    '.JPG', '.JPEG', '.PNG', '.WEBP'
}

def scan_images(directory: str) -> List[Path]:
    """
    扫描目录，返回按文件名排序的图片文件列表

    Args:
        directory: 图片目录路径

    Returns:
        排序后的 Path 对象列表
    """
    dir_path = Path(directory)

    if not dir_path.exists():
        raise FileNotFoundError(f"目录不存在: {directory}")

    if not dir_path.is_dir():
        raise NotADirectoryError(f"路径不是目录: {directory}")

    files = []
    for ext in SUPPORTED_EXTENSIONS:
        files.extend(dir_path.glob(f"*{ext}"))

    # 按文件名排序（保持可预测的顺序）
    files.sort(key=lambda p: p.name.lower())

    logger.info(f"扫描目录 '{directory}': 找到 {len(files)} 个图片文件")
    return files

def generate_combinations(pic1_files: List[Path], pic2_files: List[Path]) -> List[Tuple[Path, Path]]:
    """
    生成所有配对组合（笛卡尔积）

    Args:
        pic1_files: 第一组图片列表
        pic2_files: 第二组图片列表

    Returns:
        组合列表 [(pic1, pic2), ...]
    """
    combinations = []
    for f1 in pic1_files:
        for f2 in pic2_files:
            combinations.append((f1, f2))

    logger.info(f"生成组合: {len(pic1_files)} × {len(pic2_files)} = {len(combinations)}")
    return combinations

def build_output_name(pic1: Path, pic2: Path, extension: str = "jpg") -> str:
    """
    构建输出文件名

    规则: pic1文件名(不含扩展)_pic2文件名(不含扩展).jpg

    Examples:
        pic1: 阿霞.jpg, pic2: 百叶窗.jpg → 阿霞_百叶窗.jpg
    """
    stem1 = pic1.stem
    stem2 = pic2.stem
    return f"{stem1}_{stem2}.{extension}"

def save_combinations(combinations: List[Tuple[Path, Path]], output_file: Path):
    """
    保存组合列表到 JSON 文件

    Args:
        combinations: 组合列表
        output_file: 输出文件路径
    """
    data = []
    for f1, f2 in combinations:
        data.append({
            "pic1": str(f1),
            "pic2": str(f2),
            "output_name": build_output_name(f1, f2)
        })

    output_file.parent.mkdir(parents=True, exist_ok=True)
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    logger.info(f"组合列表已保存: {output_file} ({len(data)} 条)")

def main():
    import yaml
    import argparse

    parser = argparse.ArgumentParser(description="扫描图片目录并生成配对组合")
    parser.add_argument("--config", default="config.yaml", help="配置文件路径")
    parser.add_argument("--pic1", help="覆盖 pic1 目录路径")
    parser.add_argument("--pic2", help="覆盖 pic2 目录路径")
    parser.add_argument("--dry-run", action="store_true", help="仅显示结果，不生成文件")
    parser.add_argument("--output", default="logs/combinations.json", help="组合列表输出路径")
    args = parser.parse_args()

    # 配置日志
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

    try:
        # 加载配置
        with open(args.config, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)

        pic1_dir = args.pic1 or config['paths']['pic1_dir']
        pic2_dir = args.pic2 or config['paths']['pic2_dir']

        # 扫描
        logger.info("=== 开始扫描 ===")
        pic1_files = scan_images(pic1_dir)
        pic2_files = scan_images(pic2_dir)

        # 输出文件列表
        print("\n[扫描结果]")
        print(f"   pic1 ({pic1_dir}): {len(pic1_files)} 张图片")
        for f in pic1_files:
            print(f"     - {f.name}")
        print(f"   pic2 ({pic2_dir}): {len(pic2_files)} 张图片")
        for f in pic2_files:
            print(f"     - {f.name}")

        # 生成组合
        combos = generate_combinations(pic1_files, pic2_files)

        print(f"\n[组合列表] 共生成 {len(combos)} 个组合:")
        for i, (f1, f2) in enumerate(combos, 1):
            output_name = build_output_name(f1, f2)
            print(f"  {i:03d}. {f1.name} + {f2.name} -> {output_name}")

        if args.dry_run:
            print("\n[完成] 扫描完成（--dry-run 模式，未生成文件）")
            return 0

        # 保存组合列表
        save_combinations(combos, Path(args.output))

        print(f"\n[完成] 组合列表已保存到: {args.output}")
        print("   接下来请运行: python scripts/runner.py")
        return 0

    except FileNotFoundError as e:
        logger.error(f"文件错误: {e}")
        return 1
    except Exception as e:
        logger.exception(f"未知错误: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
