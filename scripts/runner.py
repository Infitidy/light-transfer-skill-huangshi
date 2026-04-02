#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
RunningHub AI 应用运行器（纯 API）
封装 runninghub_app.py 和 runninghub.py 的功能
"""

import json
import logging
import sys
import time
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

# 导入 OpenClaw_RH_Skills 中的 RunningHub 模块
# 路径由 light_transfer_cli.py 统一设置，此处仅检查导入
try:
    from runninghub_app import (
        get_node_info,
        upload_file,
        submit_task as rh_submit_task,
        poll_task,
        download_file as rh_download_file,
        require_api_key,
    )
except ImportError as e:
    logger.error(f"无法导入 RunningHub 模块: {e}")
    logger.error("请确保 OpenClaw_RH_Skills 已克隆到 skills/ 目录并在 light_transfer_cli.py 中正确配置路径")
    raise

class RunningHubRunner:
    """
    图片光线迁移专用运行器
    工作流: 2037342126949797890
    节点: 8 (LoadImage.image), 9 (LoadImage.image)
    """

    def __init__(self, config: dict):
        self.config = config
        self.webapp_id = config['workflow']['workflow_id']
        self.api_key = require_api_key(None)  # 从环境/配置文件解析
        self.node_info_cache = None  # 缓存节点信息

        # 输出配置
        self.output_dir = Path(config['paths']['output_base']) / time.strftime("%Y-%m-%d")
        self.output_dir.mkdir(parents=True, exist_ok=True)

        logger.info(f"RunningHubRunner 初始化")
        logger.info(f"  webapp_id: {self.webapp_id}")
        logger.info(f"  output_dir: {self.output_dir}")

    def get_nodes(self):
        """获取工作流节点结构（带缓存）"""
        if self.node_info_cache is None:
            logger.info(f"获取工作流节点信息: {self.webapp_id}")
            self.node_info_cache = get_node_info(self.api_key, self.webapp_id)
            logger.info(f"  节点数: {len(self.node_info_cache)}")
        return self.node_info_cache

    def upload_image(self, image_path: str) -> str:
        """
        上传图片，返回 fileName（用于 fieldValue）
        注意：RunningHub 返回的 fileName 是 CDN 路径，如 "api/xxx.jpg"
        """
        logger.info(f"上传图片: {image_path}")
        filename = upload_file(self.api_key, image_path)
        logger.info(f"  上传完成: {filename}")
        return filename

    def submit_task(self, pic1_path: str, pic2_path: str, output_name: str) -> str:
        """
        提交单个组合任务

        Args:
            pic1_path: 第一张图片路径
            pic2_path: 第二张图片路径
            output_name: 期望的输出文件名（如 阿霞_百叶窗.jpg）

        Returns:
            taskid
        """
        # 1. 获取节点结构
        nodes = self.get_nodes()

        # 2. 上传图片
        fname1 = self.upload_image(pic1_path)
        fname2 = self.upload_image(pic2_path)

        # 3. 填充节点参数
        # 约定：nodeId 8 对应pic1，nodeId 9 对应pic2（需验证）
        modified = []
        for node in nodes:
            nid = node["nodeId"]
            # 复制节点对象，避免修改缓存
            new_node = node.copy()
            if nid == "8":
                new_node["fieldValue"] = fname1
            elif nid == "9":
                new_node["fieldValue"] = fname2
            modified.append(new_node)

        logger.info(f"提交任务: {Path(pic1_path).name} + {Path(pic2_path).name} → {output_name}")
        data = rh_submit_task(self.api_key, self.webapp_id, modified, "default")
        taskid = str(data["taskId"])
        logger.info(f"  任务ID: {taskid}")
        return taskid

    def wait_and_download(self, taskid: str, output_name: str, timeout: Optional[int] = None) -> Path:
        """
        轮询任务完成并下载输出（通过 subprocess 调用 poll_task.py）

        Args:
            taskid: 任务ID
            output_name: 输出文件名（如 阿霞_百叶窗.jpg）
            timeout: 超时时间（秒），默认从配置读取

        Returns:
            下载后的文件路径
        """
        import subprocess

        if timeout is None:
            timeout = self.config['processing'].get('task_timeout', 600)

        logger.info(f"等待任务完成（超时 {timeout}s）: {taskid}")

        # 调用 poll_task.py 脚本（避免其 sys.exit 退出主进程）
        script_path = Path(__file__).parent / "poll_task.py"
        cmd = [sys.executable, str(script_path), taskid]

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=timeout + 60,  # 给一点余量
                check=False
            )
        except subprocess.TimeoutExpired:
            raise RuntimeError(f"轮询超时（{timeout}s）")

        if result.returncode != 0:
            err = result.stderr.strip() or result.stdout.strip()
            raise RuntimeError(f"poll_task 失败: {err}")

        # Extract JSON from poll_task output (may be wrapped in logs)
        output = result.stdout.strip()
        first = output.find('{')
        last = output.rfind('}')
        if first == -1 or last == -1:
            raise RuntimeError("poll_task 输出中未找到 JSON 结构")
        json_text = output[first:last+1]
        try:
            final = json.loads(json_text)
        except json.JSONDecodeError as exc:
            raise RuntimeError(f"poll_task JSON 解析失败: {exc} (text snippet: {json_text[:200]}... )")

        # 提取结果 URL
        results = final.get("results", [])
        if not results:
            raise RuntimeError("任务完成但无结果输出")

        result_item = results[0]
        url = result_item.get("url") or result_item.get("outputUrl")
        if not url:
            raise RuntimeError(f"结果缺少 URL: {result_item}")

        # 下载
        output_path = self.output_dir / output_name
        logger.info(f"下载输出: {url} → {output_path}")
        rh_download_file(url, str(output_path))

        logger.info(f"[OK] 下载完成: {output_path}")
        return output_path

    def run_one(self, pic1_path: str, pic2_path: str, output_name: str) -> Optional[Path]:
        """
        完整处理单个组合

        返回: 输出文件路径，失败返回 None
        """
        try:
            taskid = self.submit_task(pic1_path, pic2_path, output_name)
            output_path = self.wait_and_download(taskid, output_name)
            return output_path
        except Exception as e:
            logger.error(f"[ERR] 任务失败: {output_name} - {e}")
            return None

# 测试函数
def test_runner():
    """快速测试 runner"""
    import yaml
    config = yaml.safe_load(open("config.yaml", "r", encoding="utf-8"))
    runner = RunningHubRunner(config)

    # 测试上传和提交（使用默认图片）
    default_pic1 = "/home/lee/光线迁移/pic1/张宁1.jpg"
    default_pic2 = "/home/lee/光线迁移/pic2/暖光斑1.jpg"

    if Path(default_pic1).exists() and Path(default_pic2).exists():
        result = runner.run_one(default_pic1, default_pic2, "test_output.jpg")
        print(f"Test result: {result}")
    else:
        print("测试图片不存在，跳过")

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    test_runner()
