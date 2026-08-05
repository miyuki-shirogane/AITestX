import subprocess
import json
import os
from langchain.tools import tool


@tool
def run_pytest(target: str = "output") -> str:
    """
    执行 pytest 测试用例，返回执行结果摘要。

    参数:
    - target: 测试文件或目录路径，如 "output/test_login.py" 或 "output/"

    返回: 测试执行结果（通过/失败数量和详情）
    """
    cmd = ["pytest", target, "-v", "--tb=short", "--no-header", "-q"]
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
    return result.stdout + "\n" + result.stderr


@tool
def get_failed_tests(target: str = "output") -> str:
    """
    获取最近一次测试执行中失败的用例列表及详细错误信息。

    参数:
    - target: 测试目录路径

    返回: JSON 格式的失败用例列表，包含文件名、用例名和错误信息
    """
    cmd = ["pytest", target, "-v", "--tb=short", "--no-header", "-q"]
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)

    output = result.stdout + result.stderr
    failures = []
    current_file = ""
    current_test = ""
    current_error = []
    in_error = False

    for line in output.split("\n"):
        if line.startswith("FAILED "):
            if current_test and current_error:
                failures.append({
                    "file": current_file,
                    "test": current_test,
                    "error": "\n".join(current_error[-20:])
                })
            parts = line.replace("FAILED ", "").strip().split("::")
            current_file = parts[0] if len(parts) > 0 else ""
            current_test = parts[1] if len(parts) > 1 else ""
            current_error = []
            in_error = False
        elif line.startswith("_") and "_.py" in line and in_error:
            current_error.append(line)
        elif line.strip() == "" and in_error:
            in_error = False
        elif current_test and (line.startswith("E ") or line.startswith("> ") or "Error" in line or "AssertionError" in line):
            in_error = True
            current_error.append(line)
        elif in_error and line.strip():
            current_error.append(line)

    if current_test and current_error:
        failures.append({
            "file": current_file,
            "test": current_test,
            "error": "\n".join(current_error[-20:])
        })

    passed = output.count("PASSED") if "PASSED" in output else output.count(".")
    total = passed + len(failures)

    summary = {
        "total": total,
        "passed": passed if isinstance(passed, int) else 0,
        "failed": len(failures),
        "failures": failures
    }
    return json.dumps(summary, indent=2, ensure_ascii=False)


@tool
def get_test_summary(target: str = "output") -> str:
    """
    获取测试执行统计摘要（仅数量，不含详细错误）。

    参数:
    - target: 测试目录路径

    返回: 通过/失败/跳过数量
    """
    cmd = ["pytest", target, "--tb=no", "--no-header", "-q"]
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
    output = result.stdout + result.stderr

    passed = output.count("PASSED")
    failed = output.count("FAILED")
    skipped = output.count("SKIPPED")

    last_line = ""
    for line in output.strip().split("\n"):
        if "passed" in line or "failed" in line:
            last_line = line.strip()

    return f"通过: {passed}, 失败: {failed}, 跳过: {skipped}\n{last_line}"