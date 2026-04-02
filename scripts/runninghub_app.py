#!/usr/bin/env python3
"""
RunningHub AI Application client for OpenClaw.

Run any RunningHub AI Application (custom ComfyUI workflow) by webappId.
Uses only Python stdlib (urllib).

Modes:
  --check                          Account health check (key + balance)
  --list [--sort S] [--size N]     Browse AI applications
  --info WEBAPP_ID                 Show app's modifiable nodes
  --run WEBAPP_ID [options]        Execute an AI application task
"""

from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path

API_HOST = "https://www.runninghub.cn"
APP_LIST_PATH = "/openapi/v2/aiapp/list"
NODE_INFO_PATH = "/api/webapp/apiCallDemo"
UPLOAD_PATH = "/task/openapi/upload"
SUBMIT_PATH = "/task/openapi/ai-app/run"

# 由 runner.py 负责添加 OpenClaw_RH_Skills/runninghub/scripts 到 sys.path
from runninghub import resolve_api_key, require_api_key, cmd_check, poll_task, fix_mov_to_mp4  # noqa: E402


# ---------------------------------------------------------------------------
# HTTP helpers (urllib-based, stdlib only)
# ---------------------------------------------------------------------------

def curl_get(url: str, timeout: int = 30):
    import urllib.request
    import ssl
    ctx = ssl.create_default_context()
    try:
        req = urllib.request.Request(url, method='GET')
        with urllib.request.urlopen(req, timeout=timeout, context=ctx) as resp:
            return type('CompletedProcess', (), {
                'stdout': resp.read().decode('utf-8'),
                'stderr': '',
                'returncode': 0
            })()
    except Exception as e:
        return type('CompletedProcess', (), {
            'stdout': '',
            'stderr': str(e),
            'returncode': 1
        })()


def curl_post_json(url: str, payload: dict, timeout: int = 60):
    import urllib.request
    import ssl
    ctx = ssl.create_default_context()
    data = json.dumps(payload).encode('utf-8')
    headers = {
        'Content-Type': 'application/json',
        'Host': urllib.parse.urlparse(url).netloc
    }
    try:
        req = urllib.request.Request(url, data=data, headers=headers, method='POST')
        with urllib.request.urlopen(req, timeout=timeout, context=ctx) as resp:
            return type('CompletedProcess', (), {
                'stdout': resp.read().decode('utf-8'),
                'stderr': '',
                'returncode': 0
            })()
    except Exception as e:
        return type('CompletedProcess', (), {
            'stdout': '',
            'stderr': str(e),
            'returncode': 1
        })()


def curl_upload(url: str, api_key: str, file_path: str, timeout: int = 120):
    import urllib.request
    import ssl
    ctx = ssl.create_default_context()

    boundary = '----WebKitFormBoundary' + os.urandom(16).hex()

    body = b''
    body += f'--{boundary}\r\n'.encode()
    body += f'Content-Disposition: form-data; name="apiKey"\r\n\r\n{api_key}\r\n'.encode()
    body += f'--{boundary}\r\n'.encode()
    body += f'Content-Disposition: form-data; name="fileType"\r\n\r\ninput\r\n'.encode()
    body += f'--{boundary}\r\n'.encode()
    body += f'Content-Disposition: form-data; name="file"; filename="{os.path.basename(file_path)}"\r\n'.encode()
    body += b'\r\n'
    with open(file_path, 'rb') as f:
        body += f.read()
    body += f'\r\n--{boundary}--\r\n'.encode()

    host = urllib.parse.urlparse(url).netloc
    headers = {
        'Content-Type': f'multipart/form-data; boundary={boundary}',
        'Host': host
    }
    try:
        req = urllib.request.Request(url, data=body, headers=headers, method='POST')
        with urllib.request.urlopen(req, timeout=timeout, context=ctx) as resp:
            return type('CompletedProcess', (), {
                'stdout': resp.read().decode('utf-8'),
                'stderr': '',
                'returncode': 0
            })()
    except Exception as e:
        return type('CompletedProcess', (), {
            'stdout': '',
            'stderr': str(e),
            'returncode': 1
        })()


def download_file(url: str, output_path: str) -> str:
    import urllib.request
    import ssl
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    ctx = ssl.create_default_context()
    try:
        req = urllib.request.Request(url, method='GET')
        with urllib.request.urlopen(req, timeout=300, context=ctx) as resp:
            with open(output_path, 'wb') as f:
                f.write(resp.read())
        return str(Path(output_path).resolve())
    except Exception as e:
        print(f"Download failed: {e}", file=sys.stderr)
        sys.exit(1)


# ---------------------------------------------------------------------------
# AI Application API functions
# ---------------------------------------------------------------------------

def _extract_webapp_id(invoke_example: str) -> str | None:
    m = re.search(r'/run/ai-app/(\d+)', invoke_example)
    return m.group(1) if m else None


def list_apps(api_key: str, sort: str = "RECOMMEND", size: int = 10,
              page: int = 1, days: int = 7) -> dict:
    url = f"{API_HOST}{APP_LIST_PATH}"
    payload = {"current": page, "size": min(size, 50), "sort": sort}
    if sort == "HOTTEST" and days:
        payload["days"] = days

    result = curl_post_json(url, payload)
    resp = json.loads(result.stdout)

    if resp.get("code") != 0:
        print(json.dumps({
            "error": "LIST_FAILED",
            "message": resp.get("msg", "Failed to list AI apps"),
        }, ensure_ascii=False), file=sys.stderr)
        sys.exit(1)

    return resp.get("data", {})


def get_node_info(api_key: str, webapp_id: str) -> list[dict]:
    url = f"{API_HOST}{NODE_INFO_PATH}?apiKey={api_key}&webappId={webapp_id}"
    result = curl_get(url)
    resp = json.loads(result.stdout)

    if resp.get("code") != 0:
        print(json.dumps({
            "error": "APP_INFO_FAILED",
            "message": resp.get("msg", "Failed to get AI app info"),
            "detail": resp,
        }, ensure_ascii=False), file=sys.stderr)
        sys.exit(1)

    node_list = resp.get("data", {}).get("nodeInfoList", [])
    if not node_list:
        print(json.dumps({
            "error": "NO_NODES",
            "message": "No modifiable nodes found for this AI app. Make sure the app has been run at least once on the web.",
        }, ensure_ascii=False), file=sys.stderr)
        sys.exit(1)

    return node_list


def upload_file(api_key: str, file_path: str) -> str:
    path = Path(file_path)
    if not path.exists():
        print(f"Error: file not found: {file_path}", file=sys.stderr)
        sys.exit(1)

    url = f"{API_HOST}{UPLOAD_PATH}"
    print(f"Uploading {path.name}...", file=sys.stderr)
    result = curl_upload(url, api_key, file_path)
    resp = json.loads(result.stdout)

    if resp.get("code") != 0 or resp.get("msg") != "success":
        print(json.dumps({
            "error": "UPLOAD_FAILED",
            "message": f"Upload failed: {resp.get('msg', resp)}",
        }, ensure_ascii=False), file=sys.stderr)
        sys.exit(1)

    file_name = resp.get("data", {}).get("fileName")
    if not file_name:
        print(json.dumps({
            "error": "UPLOAD_FAILED",
            "message": "Upload succeeded but no fileName returned",
        }, ensure_ascii=False), file=sys.stderr)
        sys.exit(1)

    print(f"Uploaded: {file_name}", file=sys.stderr)
    return file_name


def submit_task(api_key: str, webapp_id: str, node_info_list: list[dict],
                instance_type: str = "default") -> dict:
    url = f"{API_HOST}{SUBMIT_PATH}"
    payload = {
        "apiKey": api_key,
        "webappId": int(webapp_id),
        "nodeInfoList": node_info_list,
    }
    if instance_type and instance_type != "default":
        payload["instanceType"] = instance_type

    print(f"Submitting AI app task (webapp {webapp_id})...", file=sys.stderr)
    result = curl_post_json(url, payload)
    resp = json.loads(result.stdout)

    if resp.get("code") != 0:
        print(json.dumps({
            "error": "SUBMIT_FAILED",
            "message": f"Submit failed: {resp.get('msg', resp)}",
            "detail": resp,
        }, ensure_ascii=False), file=sys.stderr)
        sys.exit(1)

    data = resp.get("data", {})
    task_id = data.get("taskId")
    if not task_id:
        print(json.dumps({
            "error": "SUBMIT_FAILED",
            "message": "No taskId in response",
            "detail": resp,
        }, ensure_ascii=False), file=sys.stderr)
        sys.exit(1)

    prompt_tips_str = data.get("promptTips")
    if prompt_tips_str:
        try:
            tips = json.loads(prompt_tips_str)
            node_errors = tips.get("node_errors", {})
            if node_errors:
                print(json.dumps({
                    "error": "NODE_ERRORS",
                    "message": "Workflow has node errors",
                    "node_errors": node_errors,
                }, ensure_ascii=False), file=sys.stderr)
                sys.exit(1)
        except (json.JSONDecodeError, TypeError):
            pass

    return data


__all__ = [
    'get_node_info',
    'upload_file',
    'submit_task',
    'poll_task',
    'download_file',
    'require_api_key',
]
