#!/usr/bin/env python3
"""AITestX - AI-Native 测试平台"""

import os
import sys
import json
import glob
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

from src.generator.retriever import TestCaseRetriever
from src.generator.generator import TestCaseGenerator
from src.generator.swagger import parse_swagger
from src.generator.deps import analyze as analyze_deps
from src.agent.healer import heal_directory


def cmd_seed(retriever: TestCaseRetriever):
    seed_dir = "knowledge_base/seed_data"
    if not os.path.isdir(seed_dir):
        print(f"请先将历史用例放到 {seed_dir}/ 目录下")
        return
    retriever.load_seed_data(seed_dir)


def _validate_imports(code: str) -> str:
    """自动补全缺失的 import"""
    if "pformat" in code and "from pprint import pformat" not in code:
        code = code.replace("import logging", "from pprint import pformat\nimport logging", 1)
        if "from pprint" not in code:
            code = "from pprint import pformat\n" + code
    if "allure." in code and "import allure" not in code:
        code = code.replace("import pytest", "import allure\nimport pytest", 1)
    if "os.getenv" in code and "import os" not in code:
        code = code.replace("import pytest", "import os\nimport pytest", 1)
    if "jmespath." in code and "import jmespath" not in code:
        code = code.replace("import pytest", "import jmespath\nimport pytest", 1)
    if "io.BytesIO" in code and "import io" not in code:
        code = code.replace("import pytest", "import io\nimport pytest", 1)
    # 重复的 f\"Bearer 修复
    if 'f"Bearer {resp' in code or "f'Bearer {resp" in code:
        code = code.replace('f"Bearer {resp["data"]["accessToken"]}"', 'resp["data"]["accessToken"]')
        code = code.replace("f'Bearer {resp['data']['accessToken']}'", "resp['data']['accessToken']")
    # 通用 Bearer 修复：f"Bearer {xxx}" → xxx
    if 'f"Bearer {' in code or "f'Bearer {" in code:
        import re
        code = re.sub(r'f"Bearer \{(.+?)\}"', r'\1', code)
        code = re.sub(r"f'Bearer \{(.+?)\}'", r'\1', code)
    return code


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
    code = _validate_imports(code)
    os.makedirs("output", exist_ok=True)
    output_path = f"output/test_{filename}.py"
    output_path = output_path.replace("-", "_").replace("{", "_").replace("}", "_")
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

    deps_info = _get_deps_for_endpoint(api_doc_path)
    if deps_info:
        api_doc = f"## ⚠️ 上游依赖（必须遵守）\n{deps_info}\n\n---\n\n{api_doc}"

    generator = TestCaseGenerator()
    code = generator.generate(api_doc)
    _save_and_print(code, os.path.splitext(os.path.basename(api_doc_path))[0])


def _verify_upstream_fixture(code: str, deps_info: str) -> bool:
    """检查生成的代码是否包含上游 API 调用"""
    import re
    upstream_paths = re.findall(r'来自 `([^`]+)`', deps_info)
    for path in upstream_paths:
        keyword = path.replace(" ", "/").split("/")[-1].replace("-", "_")
        if keyword not in code and keyword.replace("_", "-") not in code:
            return False
    return True


def _get_deps_for_endpoint(md_path: str) -> str:
    """从 markdown 文件名反查 Swagger 路径，获取依赖信息"""
    try:
        from src.generator.deps import analyze as analyze_deps
        swagger_path = os.getenv("SWAGGER_PATH", "target_service/swagger.json")
        deps = analyze_deps(swagger_path)
        name = os.path.basename(md_path).replace(".md", "")

        # 读取上游 API 的文档内容
        upstream_docs = {}
        save_dir = "target_service/api"
        for d in deps:
            for p in d["params"]:
                if p["upstream"]:
                    ep_path = p["upstream"]["path"]
                    safe_name = ep_path.replace(" ", "_").replace("/", "_").replace("-", "_").replace("{", "_").replace("}", "_").strip("_")
                    doc_path = f"{save_dir}/{safe_name}.md"
                    if os.path.exists(doc_path) and safe_name not in upstream_docs:
                        with open(doc_path) as f:
                            upstream_docs[safe_name] = f.read()

        best_match = None
        best_len = 0
        for d in deps:
            api_path = d["path"].replace(" ", "_").replace("/", "_").replace("-", "_").replace("{", "_").replace("}", "_")
            if api_path == name or name == api_path:
                if len(api_path) > best_len:
                    best_match = d
                    best_len = len(api_path)
            elif api_path in name and len(api_path) > best_len:
                best_match = d
                best_len = len(api_path)
        if best_match and best_match["params"]:
            lines = []
            for p in best_match["params"]:
                if p["upstream"]:
                    ep = p["upstream"]
                    ep_safe = ep["path"].replace(" ", "_").replace("/", "_").replace("-", "_").replace("{", "_").replace("}", "_").strip("_")
                    lines.append(f"- `{p['name']}` 来自 `{ep['path']}`")
                    lines.append(f"  请生成 fixture 调用此上游接口获取真实 {p['name']}")
                    # 追加上游接口的文档
                    if ep_safe in upstream_docs:
                        lines.append(f"  上游接口文档：")
                        for doc_line in upstream_docs[ep_safe].split("\n"):
                            if doc_line.strip():
                                lines.append(f"  {doc_line}")
                        lines.append("")
            if lines:
                return "\n".join(lines)
    except Exception:
        pass
    return ""


def cmd_generate_batch():
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
        print(f" (变更: {stats['changed']}, 新增: {stats['new']}, 未变: {stats['unchanged']}, 手动修改跳过: {stats.get('user_edited', 0)})")
    else:
        user_edited = stats.get('user_edited', 0)
        if user_edited > 0:
            print(f" (手动修改跳过: {user_edited} 个)")
        else:
            print()
    save_dir = "target_service/api"
    os.makedirs(save_dir, exist_ok=True)
    for api in apis:
        doc_path = f"{save_dir}/{api['filename']}"
        with open(doc_path, "w", encoding="utf-8") as f:
            f.write(api["doc"])
        print(f"  [{api['tag']}] {api['path']} → {doc_path}")

    # 清理旧文件（不在当前 spec 中的）
    current_files = {f"{save_dir}/{api['filename']}" for api in apis}
    for old_file in glob.glob(f"{save_dir}/*.md"):
        if old_file not in current_files:
            os.remove(old_file)
            print(f"  🗑 清理旧文件: {old_file}")
    print(f"\n文档已保存到 {save_dir}/")
    print(f"批量生成: python main.py batch")
    print(f"增量更新: python main.py swagger <源> --diff")


def cmd_deps(swagger_path: str = None):
    """分析 Swagger 接口依赖关系"""
    if not swagger_path:
        swagger_path = os.getenv("SWAGGER_PATH", "target_service/swagger.json")
    deps = analyze_deps(swagger_path)

    print(f"{'接口':<60} {'参数':<20} {'上游接口'}")
    print("-" * 110)
    for d in deps:
        for p in d["params"]:
            upstream = p["upstream"]["path"] if p["upstream"] else "—"
            print(f"{d['path']:<60} {p['name']:<20} {upstream}")

    # 统计
    has_dep = sum(1 for d in deps if any(p["upstream"] for p in d["params"]))
    total = len(deps)
    print(f"\n{has_dep}/{total} 个接口有上游依赖")


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
        print("  python main.py deps                       # 分析接口上下游依赖关系")
        print("  python main.py generate <文档>              # 生成单个接口的测试用例")
        print("  python main.py batch                       # 批量生成所有接口（断点续传）")
        print("  python main.py heal [target]               # 执行测试并自动修复")
        print("  python main.py report                      # 生成自愈报告")
        return
    cmd = sys.argv[1]
    if cmd == "seed":
        retriever = TestCaseRetriever()
        cmd_seed(retriever)
    elif cmd == "swagger":
        source = sys.argv[2] if len(sys.argv) > 2 else ""
        cmd_swagger(source)
    elif cmd == "deps":
        swagger_path = sys.argv[2] if len(sys.argv) > 2 else os.getenv("SWAGGER_PATH", "target_service/swagger.json")
        cmd_deps(swagger_path)
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
    else:
        print(f"未知命令: {cmd}")


if __name__ == "__main__":
    main()