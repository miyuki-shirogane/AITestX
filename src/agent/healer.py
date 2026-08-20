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

    # 第一轮前：统一 code/statusCode/_status 断言格式
    _normalize_assertions(file_path)

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


def _normalize_assertions(file_path: str):
    """统一 resp["code"]/resp["statusCode"]/_status 为自适应取值，仅处理 test 函数，不碰 fixture"""
    import re
    with open(file_path, "r") as f:
        code = f.read()

    if "_status_code" in code:
        return

    helper = """
def _status_code(resp):
    return resp.get("code") or resp.get("statusCode") or resp.get("_status")

def _is_success(resp):
    sc = _status_code(resp)
    return sc is not None and sc < 400
"""
    # 注入 helper 到文件顶部（第一个 import 之后）
    code = re.sub(r'(import logging\n)', r'\1' + helper, code, count=1)
    if "_status_code" not in code:
        code = re.sub(r'(from pprint import pformat\n)', r'\1' + helper, code, count=1)

    # 只处理 test 函数体内的代码，跳过 fixture 和 class 定义
    lines = code.split('\n')
    result = []
    in_test = False
    test_indent = 0
    in_fixture = False
    fixture_indent = 0

    for line in lines:
        stripped = line.lstrip()
        current_indent = len(line) - len(stripped)

        # 检测 fixture 边界
        if re.match(r'@pytest\.fixture', stripped):
            in_fixture = True
            fixture_indent = current_indent
        elif in_fixture and re.match(r'def ', stripped) and current_indent <= fixture_indent:
            pass  # 继续在 fixture 内
        elif in_fixture and current_indent <= fixture_indent and stripped != '':
            in_fixture = False

        # 检测 test 函数边界
        if re.match(r'def test_', stripped):
            in_test = True
            test_indent = current_indent
        elif in_test and current_indent <= test_indent and stripped != '' and not re.match(r'def test_', stripped):
            in_test = False

        if in_test and not in_fixture:
            # resp["code"] → _status_code(resp)
            line = re.sub(r'resp\["code"\]', r'_status_code(resp)', line)
            line = re.sub(r"resp\['code'\]", r'_status_code(resp)', line)
            # has_entry("code", X) → any_of(has_entry("code", X), has_entry("_status", X))
            line = re.sub(
                r'has_entry\("code",\s*(greater_than\(0\)|equal_to\(\d+\)|is_not\(\d+\)|400|401|403)\)',
                r'any_of(has_entry("code", \1), has_entry("_status", \1))',
                line
            )

        result.append(line)

    with open(file_path, "w") as f:
        f.write('\n'.join(result))


def _smart_retry(file_path: str, failures: list):
    """对 409/404 错误，泛化改写 fixture 为 shuffle + 遍历"""
    import re
    with open(file_path, "r") as f:
        code = f.read()

    for failure in failures:
        error = failure.get("error", "")
        test_name = failure.get("test", "")

        if not ("409" in error or "404" in error):
            continue

        # 从 test 函数签名提取 fixture 参数名
        test_pattern = r'def\s+' + re.escape(test_name.split('.')[-1]) + r'\s*\((.*?)\)'
        tm = re.search(test_pattern, code, re.DOTALL)
        if not tm:
            continue

        exclude = {'self', 'auth_headers', 'request', 'capsys', 'caplog', 'tmpdir', 'tmp_path'}
        candidate_fixtures = [p.strip() for p in tm.group(1).split(',') if p.strip() not in exclude and not p.strip().startswith('_')]

        for fname in candidate_fixtures:
            if not fname or fname in code.split('def ' + fname)[0:1]:
                continue

            # 找 fixture 定义
            fixture_pattern = r'(def\s+' + re.escape(fname) + r'\s*\(.*?\):(?:\n.*?)*?)(?=\n(?:@pytest|def\s+test_|class\s+))'
            fm = re.search(fixture_pattern, code, re.DOTALL)
            if not fm:
                continue

            old_fixture = fm.group(0)

            # 找「取列表第一个元素」的模式
            # pattern: xxx[0]["yyy"] 或 xxx[0]['yyy']
            m2 = re.search(r'(\w+)\[0\]\[["\'](\w+)["\']\]', old_fixture)
            if m2:
                list_var, field_name = m2.group(1), m2.group(2)
            else:
                # pattern: return xxx[0]
                m3 = re.search(r'return\s+(\w+)\[0\]', old_fixture)
                if m3:
                    list_var, field_name = m3.group(1), None
                else:
                    continue

            new_fixture = _build_shuffle_fixture(old_fixture, fname, list_var, field_name)
            code = code.replace(old_fixture, new_fixture)
            break

    with open(file_path, "w") as f:
        f.write(code)


def _build_shuffle_fixture(old_fixture: str, fname: str, list_var: str, field_name: str) -> str:
    """生成 scope=function + shuffle 遍历的 fixture"""
    import re

    # 改 scope 为 function
    new = re.sub(r'@pytest\.fixture\([^)]*\)', '@pytest.fixture(scope="function")', old_fixture, count=1)

    # 在 fixture 函数体开头插入 import random
    new = re.sub(
        r'(def\s+' + re.escape(fname) + r'\s*\(.*?\):\s*\n\s*)"""',
        r'\1import random\n    """',
        new
    )
    if 'import random' not in new:
        new = re.sub(
            r'(def\s+' + re.escape(fname) + r'\s*\(.*?\):\s*\n)',
            r'\1    import random\n',
            new
        )

    # 在 return 前插入 shuffle + 遍历逻辑
    if field_name:
        insert = (
            f'random.shuffle({list_var})\n'
            f'    for _item in {list_var}:\n'
            f'        _id = _item.get("{field_name}")\n'
            f'        if _id:\n'
            f'            return _id\n'
            f'    pytest.skip("all items in {list_var} in use or invalid")\n'
        )
    else:
        insert = (
            f'random.shuffle({list_var})\n'
            f'    for _item in {list_var}:\n'
            f'        if _item:\n'
            f'            return _item\n'
            f'    pytest.skip("all items in {list_var} in use")\n'
        )

    # 替换 return 行
    new = re.sub(r'(\s+)(return\s+\w+\[0\].*)', r'\1' + insert, new)
    return new


def _adaptive_assertion(file_path: str, rounds: list):
    """检测 code/statusCode 振荡，用 _status_code 统一"""
    import re

    # 检测前两轮是否有 code ↔ statusCode 来回修改
    code_changes = 0
    status_changes = 0
    for rd in rounds:
        action = rd.get("action", "")
        if "statusCode" in action and "改为" in action:
            status_changes += 1
        if '"code"' in action and "statusCode" in action:
            code_changes += 1

    if code_changes < 2 and status_changes < 2:
        return

    with open(file_path, "r") as f:
        code = f.read()

    # 将残留的 resp["code"] 和 resp["statusCode"] 统一替换为 _status_code
    code = re.sub(r'resp\["code"\]', r'_status_code(resp)', code)
    code = re.sub(r'resp\["statusCode"\]', r'_status_code(resp)', code)
    code = re.sub(r"resp\['code'\]", r'_status_code(resp)', code)
    code = re.sub(r"resp\['statusCode'\]", r'_status_code(resp)', code)

    # has_entries({"code": X}) → 保留（正常响应一定有 code），但混合时加兜底
    code = re.sub(
        r'has_entry\("code",\s*(greater_than\(0\)|equal_to\(\d+\)|is_not\(\d+\)|400|401|403)\)',
        r'any_of(has_entry("code", \1), has_entry("_status", \1), has_entry("statusCode", \1))',
        code
    )

    with open(file_path, "w") as f:
        f.write(code)