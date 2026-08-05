#!/usr/bin/env python3
"""AITestX - AI-Native 测试平台"""

import os
import sys
from dotenv import load_dotenv

load_dotenv()

from src.generator.retriever import TestCaseRetriever
from src.generator.generator import TestCaseGenerator
from src.generator.swagger import parse_swagger
from src.agent.executor import TestExecutorAgent


def cmd_seed(retriever: TestCaseRetriever):
    seed_dir = "knowledge_base/seed_data"
    if not os.path.isdir(seed_dir):
        print(f"请先将历史用例放到 {seed_dir}/ 目录下")
        return
    retriever.load_seed_data(seed_dir)


def _save_and_print(code: str, filename: str):
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


def cmd_swagger(source: str):
    if not source:
        print("用法: python main.py swagger <URL或本地文件路径>")
        return

    print(f"正在解析 Swagger 文档: {source}")
    apis = parse_swagger(source)
    print(f"解析到 {len(apis)} 个接口\n")

    save_dir = "target_service/api"
    os.makedirs(save_dir, exist_ok=True)

    for api in apis:
        safe_name = api["path"].replace("/", "_").replace(" ", "_").strip("_")
        doc_path = f"{save_dir}/{safe_name}.md"
        with open(doc_path, "w", encoding="utf-8") as f:
            f.write(api["doc"])
        print(f"  [{api['tag']}] {api['path']} → {doc_path}")

    print(f"\n文档已保存到 {save_dir}/，用 python main.py generate <文件> 生成用例")


def cmd_heal(target: str = "output"):
    """执行测试并自动修复失败的用例"""
    print("=" * 60)
    print("AITestX Phase 2 - 测试执行与自愈")
    print("=" * 60)
    print(f"目标: {target}/")
    print()

    agent = TestExecutorAgent()
    report = agent.run(target)
    print("\n" + "=" * 60)
    print(report)


def main():
    if len(sys.argv) < 2:
        print("用法:")
        print("  python main.py seed                     # 加载历史用例到知识库")
        print("  python main.py swagger <URL或文件>       # 从 Swagger 解析 API 文档")
        print("  python main.py generate <文档>           # 根据 API 文档生成测试用例")
        print("  python main.py heal [target]             # 执行测试并自动修复（默认 output/）")
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
    elif cmd == "heal":
        target = sys.argv[2] if len(sys.argv) > 2 else "output"
        cmd_heal(target)
    else:
        print(f"未知命令: {cmd}")


if __name__ == "__main__":
    main()