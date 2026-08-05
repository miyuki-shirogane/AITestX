import json
import os
import time
from datetime import datetime
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain.agents import create_agent

from .tools.pytest_tools import run_pytest, get_failed_tests, get_test_summary
from .tools.file_tools import read_test_file, write_test_file
from .self_healing import analyze_failure, attempt_fix

load_dotenv()


class TestExecutorAgent:
    def __init__(self):
        self.llm = ChatOpenAI(
            model="deepseek-chat",
            api_key=os.getenv("DEEPSEEK_API_KEY"),
            base_url=os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com"),
            temperature=0,
            timeout=300,
            max_retries=2,
        )

        self.tools = [
            run_pytest,
            get_failed_tests,
            get_test_summary,
            read_test_file,
            write_test_file,
        ]

        self.system_prompt = """你是一个测试执行与自愈 Agent。

你的任务是：
1. 执行 pytest 测试用例
2. 如果有失败，逐一分析每个失败用例
3. 判断失败原因（断言值偏差 / 类型错误 / 服务 Bug / 需要上游数据）
4. 对于可自动修复的用例，修复后重跑验证
5. 最终输出结构化报告

工作流程：
- 先用 run_pytest 执行测试
- 用 get_failed_tests 获取失败详情
- 对每个失败用例，用 read_test_file 读取代码
- 分析失败原因：
  - assertion_mismatch: 断言值不对，如期望 code=0 实际是 200
  - type_error: 类型断言错误，如期望 str 实际是 dict
  - service_bug: 服务 500 错误
  - upstream_data_needed: 需要上游数据（如 location_id）
- 对于 assertion_mismatch / type_error: 用 write_test_file 修复代码，然后重跑
- 对于 service_bug / upstream_data_needed: 记录到报告，不尝试修复
- 修复后重跑验证，如果通过则记录成功，否则标记为需人工介入
- 每次只修复一个用例，修复后立即重跑验证
- 如果某个用例修复 3 次后仍失败，标记为需人工介入，不再尝试
- 最终输出完整报告，包含统计数据"""

        self.agent = create_agent(
            model=self.llm,
            tools=self.tools,
            system_prompt=self.system_prompt,
        )

    def run(self, target: str = "output") -> str:
        result = self.agent.invoke({
            "messages": [{
                "role": "user",
                "content": f"""
请对 {target}/ 目录下的所有测试用例执行测试并做自愈分析。

步骤：
1. 先执行全部测试，查看整体结果
2. 如果有失败，获取失败详情
3. 对每个失败用例：
   a. 读取用例代码
   b. 分析失败原因
   c. 如果是 assertion_mismatch（断言值偏差）或 type_error（类型错误），修复代码
   d. 修复后重跑该用例验证
   e. 如果修复后仍失败，标记为需人工介入
4. 输出最终报告，包含：
   - 总用例数、通过数、修复数、修复成功数、需人工介入数
   - 每个修复用例的详情（原始断言 vs 实际值，修复了什么）
   - 需人工介入的用例及原因
            """
            }]
        })

        messages = result.get("messages", [])
        for msg in messages:
            if hasattr(msg, "content") and msg.content:
                return msg.content
        return str(result)