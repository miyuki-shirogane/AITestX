"""Executor — 复现失败用例，获取完整证据"""

import subprocess
import sys
import re
import json


def reproduce(file_path: str, test_name: str) -> dict | None:
    """重跑单个用例，解析请求/响应/断言"""
    result = subprocess.run(
        [sys.executable, "-m", "pytest", f"{file_path}::{test_name}",
         "--tb=long", "-s", "-q", "--no-header"],
        capture_output=True, text=True, timeout=120
    )
    output = result.stdout + result.stderr

    if "PASSED" in output and "FAILED" not in output:
        return None

    evidence = {
        "test_name": test_name,
        "test_file": file_path,
        "request": {"method": "POST", "path": "", "body": {}},
        "response": {"http_status": 0, "body": {}},
        "assertion": {"line": "", "expected": "", "actual": "", "error_type": ""},
        "fixture_chain": [],
        "fixture_values": {},
    }

    # 从 stdout 日志中提取请求体和响应体
    # 日志格式: "请求: {...}" 和 "响应: {...}"
    # pformat 可能把响应体拆成多行，需要收集后续缩进行
    lines = output.split("\n")
    for i, line in enumerate(lines):
        stripped = line.strip()
        if not stripped.startswith(("请求:", "请求：", "响应:", "响应：")):
            continue
        if "pformat" in stripped or "logging" in stripped:
            continue

        is_req = stripped.startswith(("请求:", "请求："))
        prefix = "请求:" if "请求:" in stripped else "请求：" if "请求：" in stripped else "响应:" if "响应:" in stripped else "响应："
        body_str = stripped.split(prefix, 1)[1].strip() if prefix in stripped else stripped.split("：", 1)[1].strip()

        # 收集后续 pformat 续行
        for j in range(i + 1, min(i + 20, len(lines))):
            cont = lines[j]
            if cont.startswith(" ") and not cont.strip().startswith(("请求", "响应", "INFO", "=", "-")):
                body_str += cont.strip()
            elif cont.strip() == "":
                continue
            else:
                break

        target = evidence["request"]["body"] if is_req else evidence["response"]["body"]
        body = _try_parse_response(body_str[:2000])
        if is_req:
            evidence["request"]["body"] = body
        else:
            evidence["response"]["body"] = body

    # 提取 HTTP 状态码
    _extract_status(evidence["response"]["body"], evidence)

    # 兜底：如果日志中没有 响应: {...}，尝试从 traceback 中提取
    if not evidence["response"]["body"] or evidence["response"]["body"] == {}:
        _extract_body_from_traceback(output, evidence)

    # 从 traceback 中提取断言信息
    exp_match = re.search(r'Expected[：:]\s*(.+?)(?:\n|$)', output)
    if exp_match:
        evidence["assertion"]["expected"] = exp_match.group(1).strip()[:200]
    but_match = re.search(r'but[：:]\s*(.+?)(?:\n|$)', output)
    if but_match:
        evidence["assertion"]["actual"] = but_match.group(1).strip()[:200]

    # 错误类型
    if "AssertionError" in output:
        evidence["assertion"]["error_type"] = "AssertionError"
    elif "KeyError" in output:
        evidence["assertion"]["error_type"] = "KeyError"
    elif "TypeError" in output:
        evidence["assertion"]["error_type"] = "TypeError"

    # 提取 fixture 链
    fixtures = re.findall(r'test_\w+\[.*?\]\s+\((\w+)\)', output)
    if fixtures:
        evidence["fixture_chain"] = fixtures

    # 提取 API 路径
    path_match = re.search(r'/api/v1/[\w/\-{}]+', output)
    if path_match:
        evidence["request"]["path"] = path_match.group(0)

    return evidence


def _extract_body_from_traceback(output: str, evidence: dict):
    """兜底：从 pytest traceback 中提取响应体"""
    # 匹配 Expected: ... but: was <...> 中的实际值
    but_match = re.search(r"but:\s*was\s*<(.+?)>$", output, re.MULTILINE)
    if but_match:
        raw = but_match.group(1)[:500]
        body = _try_parse_response(raw)
        evidence["response"]["body"] = body
        _extract_status(body, evidence)
        return

    # 匹配 live log 中的响应行（支持多行 pformat 输出）
    lines = output.split("\n")
    for i, line in enumerate(lines):
        if "INFO" in line and "root:" in line and ("响应:" in line or "响应：" in line):
            raw = line.split("响应:", 1)[-1] if "响应:" in line else line.split("响应：", 1)[-1]
            raw = raw.strip()
            # 收集后续缩进的行（pformat 的续行）
            for j in range(i + 1, min(i + 20, len(lines))):
                cont = lines[j]
                if cont.startswith(" ") or cont.startswith("\t"):
                    raw += cont.strip()
                elif cont.strip() == "":
                    continue
                else:
                    break
            body = _try_parse_response(raw[:2000])
            evidence["response"]["body"] = body
            _extract_status(body, evidence)
            return


def _try_parse_response(raw: str) -> dict:
    """尝试解析响应体，支持 Python dict 字面量格式"""
    try:
        return json.loads(raw)
    except (json.JSONDecodeError, ValueError):
        pass
    try:
        return json.loads(raw.replace("'", '"'))
    except (json.JSONDecodeError, ValueError):
        pass
    return {"raw": raw}


def _extract_status(body: dict, evidence: dict):
    for key in ("_status", "code", "statusCode"):
        if key in body and isinstance(body[key], int):
            evidence["response"]["http_status"] = body[key]
            return
    raw = body.get("raw", "")
    if not raw:
        raw = str(body)
    for key in ("_status", "code", "statusCode"):
        m = re.search(rf"['\"]?{key}['\"]?\s*[:=]\s*(\d+)", raw)
        if m:
            evidence["response"]["http_status"] = int(m.group(1))
            return