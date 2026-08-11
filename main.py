#!/usr/bin/env python3
"""AITestX - AI-Native 测试平台"""

import os
import sys
import json
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

from src.generator.retriever import TestCaseRetriever
from src.generator.generator import TestCaseGenerator
from src.generator.swagger import parse_swagger
from src.agent.healer import heal_directory
from src.orchestrator import orchestrate


def cmd_seed(retriever: TestCaseRetriever):
    seed_dir = "knowledge_base/seed_data"
    if not os.path.isdir(seed_dir):
        print(f"请先将历史用例放到 {seed_dir}/ 目录下")
        return
    retriever.load_seed_data(seed_dir)


def _cleanup_test_code(code: str) -> str:
    """清理生成代码中的常见问题"""
    import re
    CORE_NOUNS = ["design", "task", "file", "asset", "location", "npc", "agent", "photo", "message", "thread", "room", "house", "preset", "layout", "job", "employment", "notice", "redpacket", "friend", "invitation", "wallet", "adventure", "log", "news", "order", "product", "user", "code", "token"]

    def _replace_env_id(m):
        var_name = m.group(1).lower().replace("test_", "")
        keyword = None
        for noun in CORE_NOUNS:
            if noun in var_name:
                keyword = noun
                break
        if keyword:
            return f'"valid_{keyword}_id"'
        return m.group(0)  # 不替换，保留原样

    # 只替换 TEST_XXX_ID 结尾的变量
    code = re.sub(r'os\.getenv\("(TEST_\w+ID)"(?:,\s*"[^"]*")?\)', _replace_env_id, code)
    code = re.sub(r"os\.getenv\('(TEST_\w+ID)'(?:,\s*'[^']*')?\)", _replace_env_id, code)
    return code


def _save_and_print(code: str, filename: str):
    code = _cleanup_test_code(code)
    os.makedirs("output", exist_ok=True)
    output_path = f"output/test_{filename}.py"
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(code)
    print(f"测试用例已生成: {output_path}")
    print("-" * 60)
    print(code)


def cmd_generate(api_doc_path: str):
    if not os.path.exists(api_doc_path):
        print(f"文件不存在: {api_doc_path}")
        return
    with open(api_doc_path, "r", encoding="utf-8") as f:
        api_doc = f.read()
    generator = TestCaseGenerator()
    code = generator.generate(api_doc)
    _save_and_print(code, os.path.splitext(os.path.basename(api_doc_path))[0])


def cmd_generate_batch():
    import glob
    md_files = sorted(glob.glob("target_service/api/*.md"))
    if not md_files:
        print("没有找到 API 文档，请先运行 python main.py swagger")
        return
    checkpoint_path = "reports/gen_checkpoint.json"
    done = set()
    if os.path.exists(checkpoint_path):
        with open(checkpoint_path) as f:
            done = set(json.load(f).get("done", []))
    remaining = [f for f in md_files if os.path.basename(f) not in done]
    if not remaining:
        print("所有接口已生成完毕")
        return
    generator = TestCaseGenerator()
    total = len(remaining)
    print(f"待生成: {total} 个接口 (已生成: {len(done)} 个)")
    print("按 Ctrl+C 随时中止\n")
    for i, f in enumerate(remaining):
        name = os.path.basename(f).replace(".md", "")
        print(f"[{i+1}/{total}] {name[:55]}... ", end="", flush=True)
        try:
            with open(f, "r", encoding="utf-8") as fh:
                api_doc = fh.read()
            code = generator.generate(api_doc)
            _save_and_print(code, name)
            print("OK")
            done.add(os.path.basename(f))
            with open(checkpoint_path, "w") as cf:
                json.dump({"done": list(done)}, cf, ensure_ascii=False)
        except KeyboardInterrupt:
            print("\n\n⏸️ 已中止，进度已保存")
            return
        except Exception as e:
            print(f"FAIL: {e}")
    print(f"\n=== 完成: {len(done)} 个接口 ===")


def cmd_swagger(source: str):
    if not source:
        print("用法: python main.py swagger <URL或本地文件路径> [--diff]")
        print("  --diff  只更新变更的接口，跳过未改动的")
        return
    diff_only = "--diff" in sys.argv
    print(f"正在解析 Swagger 文档: {source}")
    apis, stats = parse_swagger(source, diff_only=diff_only)
    print(f"解析到 {stats['total']} 个接口", end="")
    if diff_only:
        print(f" (变更: {stats['changed']}, 新增: {stats['new']}, 未变: {stats['unchanged']})")
    else:
        print()
    save_dir = "target_service/api"
    os.makedirs(save_dir, exist_ok=True)
    for api in apis:
        doc_path = f"{save_dir}/{api['filename']}"
        with open(doc_path, "w", encoding="utf-8") as f:
            f.write(api["doc"])
        print(f"  [{api['tag']}] {api['path']} → {doc_path}")
    print(f"\n文档已保存到 {save_dir}/")
    print(f"批量生成: python main.py batch")
    print(f"增量更新: python main.py swagger <源> --diff")


def cmd_heal(target: str = "output"):
    print("=" * 60)
    print("AITestX Phase 2 - 测试执行与自愈")
    print("=" * 60)
    print(f"目标: {target}/")
    print("按 Ctrl+C 随时中止，进度自动保存\n")
    heal_directory(target)


def cmd_report():
    from src.agent.healer import load_results, load_checkpoint
    results = load_results()
    cp = load_checkpoint()
    if not results and not cp.get("processed"):
        print("还没有自愈记录，请先运行 python main.py heal")
        return
    stats = cp.get("stats", {})
    md = f"""# AITestX Phase 2 自愈报告

> 生成时间: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

## 概览

| 指标 | 数量 |
|------|:---:|
| 已通过文件 | {len(cp.get('processed', []))} |
| 全部通过 | {stats.get('passed', 0)} |
| 修复通过 | {stats.get('fixed', 0)} |
| 转移到 Phase 3 | {stats.get('failed', 0)} |
"""
    report_path = "reports/heal_report.md"
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(md)
    print(f"报告已生成: {report_path}")


def main():
    if len(sys.argv) < 2:
        print("用法:")
        print("  python main.py seed                        # 加载历史用例到知识库")
        print("  python main.py swagger <URL或文件> [--diff]  # 解析 Swagger（--diff 增量更新）")
        print("  python main.py generate <文档>              # 生成单个接口的测试用例")
        print("  python main.py batch                       # 批量生成所有接口（断点续传）")
        print("  python main.py heal [target]               # 执行测试并自动修复")
        print("  python main.py report                      # 生成自愈报告")
        print("  python main.py orchestrate                 # Phase 3: 上游依赖编排")
        return
    cmd = sys.argv[1]
    if cmd == "seed":
        retriever = TestCaseRetriever()
        cmd_seed(retriever)
    elif cmd == "swagger":
        source = sys.argv[2] if len(sys.argv) > 2 else ""
        cmd_swagger(source)
    elif cmd == "generate":
        if len(sys.argv) < 3:
            print("用法: python main.py generate <API文档路径>")
            return
        cmd_generate(sys.argv[2])
    elif cmd == "batch":
        cmd_generate_batch()
    elif cmd == "heal":
        target = sys.argv[2] if len(sys.argv) > 2 else "output"
        cmd_heal(target)
    elif cmd == "report":
        cmd_report()
    elif cmd == "orchestrate":
        orchestrate()
    else:
        print(f"未知命令: {cmd}")


if __name__ == "__main__":
    main()