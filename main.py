#!/usr/bin/env python3
"""AITestX - AI-Native 测试平台"""

import os
import sys
from dotenv import load_dotenv

load_dotenv()

from src.generator.retriever import TestCaseRetriever
from src.generator.generator import TestCaseGenerator


def cmd_seed(retriever: TestCaseRetriever):
    """加载历史用例到知识库"""
    seed_dir = "knowledge_base/seed_data"
    if not os.path.isdir(seed_dir):
        print(f"请先将历史用例放到 {seed_dir}/ 目录下")
        return
    retriever.load_seed_data(seed_dir)


def cmd_generate(api_doc_path: str):
    """根据API文档生成测试用例"""
    if not os.path.exists(api_doc_path):
        print(f"文件不存在: {api_doc_path}")
        return

    with open(api_doc_path, "r", encoding="utf-8") as f:
        api_doc = f.read()

    generator = TestCaseGenerator()
    code = generator.generate(api_doc)

    os.makedirs("output", exist_ok=True)
    output_path = f"output/test_{os.path.splitext(os.path.basename(api_doc_path))[0]}.py"
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(code)

    print(f"测试用例已生成: {output_path}")
    print("-" * 60)
    print(code)


def main():
    if len(sys.argv) < 2:
        print("用法:")
        print("  python main.py seed              # 加载历史用例到知识库")
        print("  python main.py generate <文档>    # 根据API文档生成测试用例")
        return

    cmd = sys.argv[1]

    if cmd == "seed":
        retriever = TestCaseRetriever()
        cmd_seed(retriever)
    elif cmd == "generate":
        if len(sys.argv) < 3:
            print("用法: python main.py generate <API文档路径>")
            return
        cmd_generate(sys.argv[2])
    else:
        print(f"未知命令: {cmd}")


if __name__ == "__main__":
    main()