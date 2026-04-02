#!/usr/bin/env python3
"""
智能轮询 RunningHub 任务状态脚本（v2）
用法:
  python poll_task.py <taskid> [--json <path>] [--log <file>]
  --json: 提供 JSON 文件路径，用于预估时长（基于 juben 字符数）
"""
import json, sys, time, os, subprocess, tempfile
from pathlib import Path

BASE_URL = "https://www.runninghub.cn/openapi/v2"
POLL_ENDPOINT = "/query"

# 基准速度（字符/秒）—— 基于第3章数据：757字 / 425秒
BASE_SPEED = 1.78

# 阶段配置
STAGE_A_DURATION = 90      # 阶段A：启动检测，持续90秒
STAGE_A_INTERVAL = 30      # 阶段A：每30秒轮询一次
STAGE_B_INTERVAL_FACTOR = 6  # 阶段B：间隔 = 预估时长/6，最小60秒
STAGE_C_THRESHOLD = 0.9    # 阶段C：进入最后10%时
STAGE_C_INTERVAL = 60      # 阶段C：每60秒轮询一次

def resolve_api_key() -> str | None:
    env_key = os.environ.get("RUNNINGHUB_API_KEY", "").strip()
    if env_key:
        return env_key
    cfg_path = Path.home() / ".openclaw" / "openclaw.json"
    if cfg_path.exists():
        try:
            cfg = json.loads(cfg_path.read_text(encoding="utf-8"))
            entry = cfg.get("skills", {}).get("entries", {}).get("runninghub", {})
            api_key = entry.get("apiKey") or entry.get("env", {}).get("RUNNINGHUB_API_KEY")
            if isinstance(api_key, str) and api_key.strip():
                return api_key.strip()
        except Exception:
            pass
    return None

def curl_post_json(url: str, payload: dict, headers: dict, timeout: int = 30):
    import urllib.request
    import ssl
    import urllib.parse
    ctx = ssl.create_default_context()
    data = json.dumps(payload).encode('utf-8')
    try:
        req = urllib.request.Request(url, data=data, headers=headers, method='POST')
        with urllib.request.urlopen(req, timeout=timeout, context=ctx) as resp:
            class Result:
                pass
            result = Result()
            result.stdout = resp.read().decode('utf-8')
            result.stderr = ''
            result.returncode = 0
            return result
    except Exception as e:
        class Result:
            pass
        result = Result()
        result.stdout = ''
        result.stderr = str(e)
        result.returncode = 1
        return result

def query_task(api_key: str, task_id: str):
    url = f"{BASE_URL}{POLL_ENDPOINT}"
    headers = {"Content-Type": "application/json", "Authorization": f"Bearer {api_key}"}
    result = curl_post_json(url, {"taskId": task_id}, headers, timeout=30)
    if result.returncode != 0:
        return None
    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError:
        return None

def estimate_from_json(json_path: str) -> int:
    """预估任务时长（秒）"""
    try:
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        juben = data.get('juben', '')
        chars = len(juben)
        estimated = int(chars / BASE_SPEED)
        return max(estimated, 60)  # 至少60秒
    except Exception:
        return 600  # 默认10分钟

def main():
    if len(sys.argv) < 2:
        print("Usage: python poll_task.py <taskid> [--json <path>] [--log <file>]")
        sys.exit(1)

    taskid = sys.argv[1]
    json_path = None
    log_file = None

    args = sys.argv[2:]
    if "--json" in args:
        idx = args.index("--json")
        json_path = args[idx+1]
    if "--log" in args:
        idx = args.index("--log")
        log_file = args[idx+1]

    def log(msg: str):
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        line = f"[{timestamp}] {msg}"
        print(line)
        if log_file:
            with open(log_file, "a", encoding="utf-8") as f:
                f.write(line + "\n")

    # 计算预估时长
    estimated_total = estimate_from_json(json_path) if json_path else 600
    log(f"Task {taskid} estimated duration: {estimated_total}s ({estimated_total/60:.1f} min)")

    api_key = resolve_api_key()
    if not api_key:
        log("ERROR: No API key configured")
        sys.exit(1)

    log("Starting smart poll...")
    start_time = time.time()
    stage_start = start_time

    while True:
        elapsed = time.time() - start_time

        # 确定当前阶段和轮询间隔
        if elapsed < STAGE_A_DURATION:
            stage_name = "A"
            interval = STAGE_A_INTERVAL
        elif elapsed < estimated_total * STAGE_C_THRESHOLD:
            stage_name = "B"
            interval = max(int(estimated_total / STAGE_B_INTERVAL_FACTOR), 60)
        else:
            stage_name = "C"
            interval = STAGE_C_INTERVAL

        if elapsed >= estimated_total:
            log(f"WARNING: Exceeded estimated duration, switching to 60s interval")
            interval = 60

        time.sleep(interval)

        resp = query_task(api_key, taskid)
        if resp is None:
            log(f"[Stage {stage_name}] Poll failed at {elapsed:.0f}s")
            continue

        status = resp.get("status")
        log(f"[Stage {stage_name}] Status: {status} (elapsed: {elapsed:.0f}s)")

        if status == "SUCCESS":
            log(f"Task completed after {elapsed:.0f}s")
            print(json.dumps(resp, ensure_ascii=False, indent=2))
            break

        if status == "FAILED":
            error_msg = resp.get("errorMessage", "Unknown error")
            error_code = resp.get("errorCode", "")
            log(f"ERROR: Task failed - [{error_code}] {error_msg}")
            print(json.dumps({
                "error": "TASK_FAILED",
                "message": f"[{error_code}] {error_msg}",
                "taskId": taskid
            }, ensure_ascii=False))
            sys.exit(1)

if __name__ == "__main__":
    main()