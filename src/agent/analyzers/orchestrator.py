"""多 Agent 失败用例分析 — 编排器"""

import json
import os
import subprocess
import sys
import glob
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime

from .base import BaseAgent, _parse_json_response
from . import executor as exe
from . import triage as tr
from . import contract as ct
from . import data_path as dp
from . import environment as env
from . import coordinator as coord

OUTPUT_DIR = "output"
REPORT_PATH = "reports/analyze_report.md"
TRACE_PATH = "reports/analyze_trace.log"


# ═══════════════════════════════════════════════════════════
# 步骤 1：发现失败用例
# ═══════════════════════════════════════════════════════════

def _discover_failures() -> tuple[list, str]:
    """运行 pytest 发现所有失败用例，返回 [(file, test_name, error), ...] 和 pytest 原始输出"""
    files = sorted(glob.glob(f"{OUTPUT_DIR}/test_*.py"))
    if not files:
        print("没有找到测试文件")
        return [], ""

    result = subprocess.run(
        [sys.executable, "-m", "pytest"] + files + ["-v", "--tb=line", "-q"],
        capture_output=True, text=True, timeout=300
    )
    output = result.stdout + result.stderr

    failures = []
    for line in output.split("\n"):
        if line.startswith("FAILED "):
            parts = line.split(" ", 1)
            if len(parts) > 1:
                full = parts[1].strip()
                if "::" in full:
                    file_path, test_name = full.split("::", 1)
                    failures.append((file_path, test_name, ""))

    return failures, output


# ═══════════════════════════════════════════════════════════
# 步骤 2：对单个失败用例执行分析
# ═══════════════════════════════════════════════════════════

def _analyze_single_failure(file_path: str, test_name: str, trace_lines: list) -> dict:
    """对单个失败用例执行完整分析流程，同时写入 trace 日志"""
    print(f"  🔍 {test_name.split('.')[-1]}")
    trace_lines.append(f"\n{'='*60}")
    trace_lines.append(f"失败用例: {test_name}")
    trace_lines.append(f"文件: {file_path}")
    trace_lines.append(f"{'='*60}")

    # 2a. Executor 复现（串行，必须先跑）
    print(f"     ⚡ Executor 复现中...")
    evidence = exe.reproduce(file_path, test_name)
    if not evidence:
        trace_lines.append("❌ Executor 复现失败")
        return {"error": "Executor 复现失败", "test_name": test_name}

    trace_lines.append(f"\n--- Executor 证据 ---")
    trace_lines.append(f"HTTP 状态: {evidence['response']['http_status']}")
    trace_lines.append(f"响应体: {json.dumps(evidence['response']['body'], ensure_ascii=False, indent=2)}")
    trace_lines.append(f"断言期望: {evidence['assertion']['expected']}")
    trace_lines.append(f"实际值: {evidence['assertion']['actual']}")
    trace_lines.append(f"错误类型: {evidence['assertion']['error_type']}")
    trace_lines.append(f"Fixture 链: {evidence['fixture_chain']}")

    print(f"     ├─ HTTP {evidence['response']['http_status']} | "
          f"断言: {evidence['assertion']['expected']} → 实际: {evidence['assertion']['actual']}")

    # 2b. 四个分析 Agent 并行
    agents = [
        tr.TriageSpecialist(),
        ct.ContractAnalyst(),
        dp.DataPathTracer(),
        env.EnvironmentChecker(),
    ]

    opinions = {}
    with ThreadPoolExecutor(max_workers=4) as pool:
        futures = {pool.submit(agent.run, evidence): agent.name for agent in agents}
        for future in as_completed(futures):
            name = futures[future]
            try:
                opinions[name] = future.result()
                trace_lines.append(f"\n--- {name} ---")
                trace_lines.append(json.dumps(opinions[name], ensure_ascii=False, indent=2))
                verdict = opinions[name].get("verdict", "?")
                confidence = opinions[name].get("confidence", "?")
                print(f"     ├─ {name}: {verdict} ({confidence})")
            except Exception as e:
                trace_lines.append(f"\n--- {name} ---\n❌ {e}")
                print(f"     ├─ {name}: ❌ {e}")
                opinions[name] = {"error": str(e)}

    # 2c. Coordinator 汇总
    print(f"     └─ Coordinator 汇总中...")
    coordinator = coord.Coordinator()
    verdict = coordinator.run(evidence, opinions)
    trace_lines.append(f"\n--- Coordinator 最终裁决 ---")
    trace_lines.append(json.dumps(verdict, ensure_ascii=False, indent=2))

    return {
        "test_name": test_name,
        "file": file_path,
        "evidence": evidence,
        "opinions": opinions,
        "verdict": verdict,
    }


# ═══════════════════════════════════════════════════════════
# 步骤 3：生成 Markdown 报告
# ═══════════════════════════════════════════════════════════

def _generate_report(results: list[dict], failures: list) -> str:
    lines = []
    lines.append("# 失败用例分析报告")
    lines.append(f"> 分析时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append(f"> 总失败: {len(failures)} 个\n")

    # 按 verdict 分组
    groups = {
        "needs_manual": [], "assertion_fix": [], "auto_fix": [],
        "ignore": [], "env_issue": [], "data_issue": [], "unknown": [],
    }
    for r in results:
        v = r.get("verdict", {}).get("final_verdict", "unknown")
        groups.setdefault(v, []).append(r)

    if groups.get("needs_manual"):
        lines.append("## 🔴 需人工介入\n")
        for r in groups["needs_manual"]:
            v = r.get("verdict", {})
            tn = r["test_name"].split(".")[-1]
            lines.append(f"### {tn}")
            lines.append(f"- **文件**: `{r['file']}`")
            lines.append(f"- **风险**: {v.get('risk_level', '')}")
            lines.append(f"- **原因**: {v.get('reasoning', '')}")
            if v.get("fix_suggestion"):
                lines.append(f"- **建议**: {v['fix_suggestion']}")
            lines.append("")

    if groups.get("assertion_fix") or groups.get("auto_fix"):
        lines.append("## 🟡 可修复\n")
        for r in (groups.get("assertion_fix", []) + groups.get("auto_fix", [])):
            v = r.get("verdict", {})
            tn = r["test_name"].split(".")[-1]
            lines.append(f"### {tn}")
            lines.append(f"- **文件**: `{r['file']}`")
            lines.append(f"- **修复**: {v.get('fix_suggestion', v.get('reasoning', ''))}")
            lines.append("")

    if groups.get("env_issue"):
        lines.append("## 🔵 环境问题\n")
        for r in groups["env_issue"]:
            v = r.get("verdict", {})
            tn = r["test_name"].split(".")[-1]
            lines.append(f"### {tn}")
            lines.append(f"- **文件**: `{r['file']}`")
            lines.append(f"- **风险**: {v.get('risk_level', '')}")
            lines.append(f"- **原因**: {v.get('reasoning', '')}")
            if v.get("fix_suggestion"):
                lines.append(f"- **建议**: {v['fix_suggestion']}")
            lines.append("")

    if groups.get("ignore"):
        lines.append("## 🟢 已知可忽略\n")
        for r in groups["ignore"]:
            v = r.get("verdict", {})
            tn = r["test_name"].split(".")[-1]
            lines.append(f"### {tn}")
            lines.append(f"- **原因**: {v.get('reasoning', '')}")
            lines.append("")

    if groups.get("unknown"):
        lines.append("## ⚪ 无法判断\n")
        for r in groups["unknown"]:
            tn = r["test_name"].split(".")[-1]
            lines.append(f"- {tn}")
        lines.append("")

    return "\n".join(lines)


# ═══════════════════════════════════════════════════════════
# 主入口
# ═══════════════════════════════════════════════════════════

def analyze(target_dir: str = "output"):
    print("=" * 60)
    print("AITestX 失败用例分析")
    print("=" * 60)

    # 1. 发现失败
    print("\n[1/3] 发现失败用例...")
    failures, pytest_output = _discover_failures()
    if not failures:
        print("没有失败用例")
        return

    print(f"发现 {len(failures)} 个失败用例\n")

    # 2. 逐个分析
    print("[2/3] 分析中...\n")
    trace_lines = [f"# AITestX 分析追踪日志",
                   f"# 时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
                   f"# 失败用例数: {len(failures)}",
                   "",
                   "## 原始 pytest 输出",
                   "```",
                   pytest_output.strip(),
                   "```"]
    results = []
    for i, (file_path, test_name, _) in enumerate(failures):
        print(f"[{i+1}/{len(failures)}] {file_path}")
        result = _analyze_single_failure(file_path, test_name, trace_lines)
        results.append(result)
        print()

    # 3. 生成报告
    print("[3/3] 生成报告...")
    report = _generate_report(results, failures)
    os.makedirs("reports", exist_ok=True)
    with open(REPORT_PATH, "w", encoding="utf-8") as f:
        f.write(report)
    with open(TRACE_PATH, "w", encoding="utf-8") as f:
        f.write("\n".join(trace_lines))
    print(f"报告: {REPORT_PATH}")
    print(f"追踪日志: {TRACE_PATH}\n")
    print(report)