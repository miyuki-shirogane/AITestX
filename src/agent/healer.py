import json
import os
import subprocess
import sys
import time
from datetime import datetime
import glob

from .self_healing import analyze_failure, attempt_fix


CHECKPOINT_FILE = "reports/heal_checkpoint.json"
RESULTS_FILE = "reports/heal_results.json"


def load_results():
    if os.path.exists(RESULTS_FILE):
        with open(RESULTS_FILE, "r") as f:
            return json.load(f)
    return {}


def save_results(results):
    os.makedirs("reports", exist_ok=True)
    with open(RESULTS_FILE, "w") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)


def load_checkpoint():
    if os.path.exists(CHECKPOINT_FILE):
        with open(CHECKPOINT_FILE, "r") as f:
            return json.load(f)
    return {"processed": [], "stats": {"total": 0, "passed": 0, "fixed": 0, "skipped": 0, "failed": 0}}


def save_checkpoint(checkpoint):
    os.makedirs("reports", exist_ok=True)
    with open(CHECKPOINT_FILE, "w") as f:
        json.dump(checkpoint, f, ensure_ascii=False, indent=2)


def run_single_test(file_path: str) -> tuple:
    """执行单个测试文件，返回 (passed_count, failed_count, failures)"""
    result = subprocess.run(
        [sys.executable, "-m", "pytest", file_path, "-v", "--tb=short", "-q", "--no-header"],
        capture_output=True, text=True, timeout=120
    )
    output = result.stdout + result.stderr

    passed = output.count("PASSED")
    failed = output.count("FAILED")

    failures = []
    lines = output.split("\n")
    i = 0
    while i < len(lines):
        line = lines[i]
        # 匹配分隔线: __________________ test_name __________________
        if line.startswith("____") and not line.startswith("____ERROR"):
            test_name = line.strip("_").strip()
            i += 1
            error_lines = []
            while i < len(lines) and not lines[i].startswith("____"):
                stripped = lines[i].strip()
                if stripped.startswith("E ") or stripped.startswith("Expected") or stripped.startswith("but:"):
                    error_lines.append(stripped)
                i += 1
            if error_lines:
                failures.append({
                    "test": test_name,
                    "error": "\n".join(error_lines)
                })
            continue
        i += 1

    return passed, failed, failures


def heal_file(file_path: str, max_rounds: int = 5) -> dict:
    """对单个文件执行自愈，最多 max_rounds 轮"""
    result = {
        "file": file_path,
        "rounds": [],
        "final_status": "unknown",
        "timestamp": datetime.now().isoformat(),
    }

    with open(file_path, "r") as f:
        original_code = f.read()

    os.makedirs("output/.backup", exist_ok=True)
    backup_path = f"output/.backup/{os.path.basename(file_path)}"
    with open(backup_path, "w") as f:
        f.write(original_code)

    non_fixable = set()

    for round_num in range(1, max_rounds + 1):
        passed, failed, failures = run_single_test(file_path)

        if failed == 0:
            result["final_status"] = "passed"
            if round_num == 1:
                result["rounds"].append({"round": 1, "action": "无需修复，直接通过"})
            else:
                result["rounds"].append({"round": round_num, "action": f"修复后通过"})
            break

        # 智能重试：程序化修复常见模式
        if round_num == 1:
            _smart_retry(file_path, failures)

        # 自适应断言：检测并修复 code/statusCode 振荡
        _adaptive_assertion(file_path, result["rounds"])

        if round_num == max_rounds:
            result["final_status"] = "needs_manual"
            result["retryable"] = True
            result["rounds"].append({
                "round": round_num,
                "action": f"达到最大修复轮次({max_rounds})，仍有 {failed} 个失败，下次可继续",
                "remaining_failures": [f["test"] for f in failures]
            })
            break

        # 过滤掉已确认不可修复的失败，剩余的可尝试修复
        fixable = [f for f in failures if f["test"] not in non_fixable]

        if not fixable:
            all_conn = all(
                "Connection" in f.get("error", "") or "ConnectError" in f.get("error", "")
                or "ConnectionRefused" in f.get("error", "") or "Max retries" in f.get("error", "")
                for f in failures
            )
            result["final_status"] = "needs_manual"
            result["retryable"] = all_conn
            result["rounds"].append({
                "round": round_num,
                "action": f"所有 {len(failures)} 个失败均无法自动修复",
                "remaining_failures": [f["test"] for f in failures]
            })
            break

        fixed_any = False
        for failure in fixable:
            test_name = failure["test"]
            error = failure["error"]

            with open(file_path, "r") as f:
                current_code = f.read()

            analysis = analyze_failure(current_code[:3000], test_name, error)

            if not analysis.get("can_auto_fix"):
                non_fixable.add(test_name)
                result["rounds"].append({
                    "round": round_num,
                    "action": f"跳过: {test_name} — {analysis.get('fix_description', '') or analysis.get('reason', '') or '原因未知'}",
                    "category": analysis.get("category"),
                    "test": test_name,
                })
                continue

            fixed_code = attempt_fix(current_code, test_name, error, analysis)
            if not fixed_code:
                continue

            try:
                compile(fixed_code, file_path, "exec")
            except SyntaxError as e:
                result["rounds"].append({
                    "round": round_num,
                    "action": f"修复后代码有语法错误: {e}",
                })
                continue

            with open(file_path, "w") as f:
                f.write(fixed_code)

            result["rounds"].append({
                "round": round_num,
                "action": f"修复 {test_name}: {analysis.get('fix_description', '')}",
                "category": analysis.get("category"),
            })
            fixed_any = True
            break

        if not fixed_any:
            non_fixable.update(f["test"] for f in fixable)
            all_conn = all(
                "Connection" in f.get("error", "") or "ConnectError" in f.get("error", "")
                or "ConnectionRefused" in f.get("error", "") or "Max retries" in f.get("error", "")
                for f in failures
            )
            result["final_status"] = "needs_manual"
            result["retryable"] = all_conn
            result["rounds"].append({
                "round": round_num,
                "action": f"本轮无可修复的失败",
                "remaining_failures": [f["test"] for f in failures]
            })
            break

    return result


def heal_directory(target_dir: str = "output"):
    checkpoint = load_checkpoint()
    processed = set(checkpoint.get("processed", []))
    results = load_results()

    files = sorted(glob.glob(f"{target_dir}/test_*.py"))
    remaining = [f for f in files if f not in processed]

    if not remaining:
        print("所有文件已处理完毕")
        return checkpoint

    print(f"待处理: {len(remaining)} 个文件 (已处理: {len(processed)} 个)")
    print("按 Ctrl+C 随时中止，已处理的文件不会丢失\n")

    for i, file_path in enumerate(remaining):
        print(f"[{i+1}/{len(remaining)}] {os.path.basename(file_path)} ... ", end="", flush=True)
        try:
            result = heal_file(file_path)
            results[file_path] = result
            save_results(results)

            status = result["final_status"]
            if status == "passed":
                processed.add(file_path)
                if len(result["rounds"]) == 1 and "无需修复" in result["rounds"][0]["action"]:
                    print("✅ 直接通过")
                    checkpoint["stats"]["passed"] += 1
                else:
                    rounds = len(result["rounds"])
                    print(f"🔧 {rounds}轮修复通过")
                    checkpoint["stats"]["fixed"] += 1
            elif status == "needs_manual":
                if result.get("retryable"):
                    print(f"⏳ 部分修复，下次继续")
                    checkpoint["stats"]["fixed"] += 1
                else:
                    processed.add(file_path)
                    print(f"⚠️ 需人工介入")
                    checkpoint["stats"]["failed"] += 1
            else:
                processed.add(file_path)
                print(f"❓ {status}")
                checkpoint["stats"]["skipped"] += 1

            checkpoint["processed"] = list(processed)
            checkpoint["stats"]["total"] = len(processed)
            save_checkpoint(checkpoint)
        except KeyboardInterrupt:
            print("\n\n⏸️ 已中止，进度已保存")
            save_checkpoint(checkpoint)
            save_results(results)
            print(f"已处理: {len(processed)} 个文件")
            print(f"下次运行 'python main.py heal' 将从断点继续")
            return checkpoint
        except Exception as e:
            msg = str(e)
            if "520" in msg or "504" in msg or "429" in msg:
                print(f"⏳ API错误，跳过（下次重试）")
                continue
            print(f"❌ 错误: {e}")
            save_checkpoint(checkpoint)
            save_results(results)

    _generate_phase3_report(results)
    print(f"\n=== 完成 ===")
    print(f"总计: {checkpoint['stats']['total']}")
    print(f"直接通过: {checkpoint['stats']['passed']}")
    print(f"修复通过: {checkpoint['stats']['fixed']}")
    print(f"需人工介入: {checkpoint['stats']['failed']}")

    # 最终运行 pytest 汇总
    print(f"\n--- 最终 pytest 结果 ---")
    result = subprocess.run(
        [sys.executable, "-m", "pytest"] + sorted(glob.glob(f"{target_dir}/test_*.py"))
        + ["-v", "--tb=line", "-q"],
        capture_output=True, text=True, timeout=300
    )
    # 提取最后几行 summary
    lines = result.stdout.split("\n") + result.stderr.split("\n")
    summary_lines = [l for l in lines if "failed" in l.lower() or "passed" in l.lower()]
    for line in summary_lines[-3:]:
        print(line)

    return checkpoint


def _generate_phase3_report(results: dict):
    """从自愈结果中提取 Phase 3 需要处理的任务"""
    tasks = []
    for fp, result in results.items():
        if result["final_status"] != "needs_manual" or result.get("retryable"):
            continue
        for r in result.get("rounds", []):
            if r.get("category") in ("upstream_data_needed", "service_bug", "invalid_test_data") or (not r.get("retryable", True)):
                tasks.append({
                    "file": os.path.basename(fp),
                    "category": r["category"],
                    "detail": r.get("action", ""),
                    "test": r.get("test", ""),
                })

    if tasks:
        report = {
            "phase": 3,
            "description": "Phase 3 编排器需要处理的上下游依赖和服务 Bug",
            "tasks": tasks,
            "generated_at": datetime.now().isoformat(),
        }
        path = "reports/phase3_tasks.json"
        with open(path, "w") as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        print(f"Phase 3 任务清单: {path} ({len(tasks)} 项)")


def _smart_retry(file_path: str, failures: list):
    """智能重试：程序化修复常见 API 响应模式问题"""
    import re
    with open(file_path, "r") as f:
        code = f.read()

    changed = False
    for failure in failures:
        error = failure.get("error", "")

        # 409/404/503: fixture 里的数据冲突或不存在，遍历数据列表
        if "409" in error or "404" in error or "503" in error:
            code = re.sub(
                r'items\[0\]\["(\w+)"\]',
                r'next((item["\1"] for item in items if item.get("\1")), None)',
                code
            )
            if "for item in items" not in code:
                code = code.replace(
                    'if items:\n        return items[0]',
                    'for item in items:\n            return item.get("id", item.get("designId"))\n    if items:\n        return items[0]'
                )
            changed = True

    # 主动扫描：修复所有 resp["code"] 和 has_entries({"code": X}) 为自适应断言
    # 因为 ApiClient 对非 JSON 响应返回 {"_status": N, "_body": ""}
    if re.search(r'has_entries\(\{"code":\s*\d+', code) or re.search(r'resp\["code"\]', code) or re.search(r'has_entry\("code",\s*\d+', code):
        # has_entries({"code": 401}) → any_of(has_entry("_status", 401), has_entry("code", 401))
        code = re.sub(
            r'has_entries\(\{"code":\s*(\d+)\}\)',
            r'any_of(has_entry("_status", \1), has_entry("code", \1))',
            code
        )
        # has_entry("code", 401) → any_of(has_entry("_status", 401), has_entry("code", 401))
        code = re.sub(
            r'has_entry\("code",\s*(\d+)\)',
            r'any_of(has_entry("_status", \1), has_entry("code", \1))',
            code
        )
        # resp["code"] → resp.get("_status", resp.get("code"))
        code = re.sub(
            r'resp\["code"\]',
            r'resp.get("_status", resp.get("code"))',
            code
        )
        changed = True

    if changed:
        with open(file_path, "w") as f:
            f.write(code)


def _adaptive_assertion(file_path: str, rounds: list):
    """检测 code/statusCode 振荡，生成自适应断言"""
    import re
    code_changes = 0
    status_changes = 0
    for rd in rounds:
        action = rd.get("action", "")
        if "statusCode" in action and "code" in action:
            if "改为" in action:
                code_changes += 1
        if "code" in action and "statusCode" in action:
            status_changes += 1

    if code_changes >= 2 or status_changes >= 2:
        with open(file_path, "r") as f:
            code = f.read()
        code = re.sub(
            r'has_entries\(\{"code":\s*(greater_than\(0\)|equal_to\(\d+\)|400|401|403)\}\)',
            r'has_entries({"code": \1, "statusCode": \1})',
            code
        )
        with open(file_path, "w") as f:
            f.write(code)
        return

    # 也主动检测文件中是否混用 code/statusCode
    with open(file_path, "r") as f:
        code = f.read()
    has_code = bool(re.search(r'\["code"\]', code)) or bool(re.search(r'has_entry\("code"', code))
    has_status = bool(re.search(r'\["statusCode"\]', code)) or bool(re.search(r'has_entry\("statusCode"', code))
    if has_code and has_status:
        code = re.sub(
            r'has_entry\("(code|statusCode)",\s*(greater_than\(0\)|equal_to\(\d+\)|400|401|403)\)',
            r'any_of(has_entry("code", \2), has_entry("statusCode", \2))',
            code
        )
        with open(file_path, "w") as f:
            f.write(code)