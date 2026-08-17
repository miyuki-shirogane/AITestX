"""Coordinator — 汇总各 Agent 意见，冲突裁决，生成最终判断"""

from langchain_core.messages import HumanMessage, SystemMessage
from .base import BaseAgent, _call_llm_with_retry, _parse_json_response

SYSTEM_PROMPT = """你是测试结果分析协调器。你综合各专家的意见，做出最终判断。

冲突裁决时，以证据为准，不以 Agent 身份为准：
- 如果某个 Agent 的结论明显与 Executor 提供的实际证据矛盾，不予采纳
- 如果多个 Agent 得出相同结论，置信度更高
- 如果 Agent 意见分歧，看谁的推理更贴近实际证据（HTTP 状态码、响应体、断言实际值）
- 不要因为某个 Agent 身份而盲目采纳其结论

具体判断：
- HTTP 状态码为 0 → 环境问题，请求未到达服务端
- HTTP 状态码为 400/401/403/404/409 → 业务逻辑问题，不是环境问题
- 响应体有 _status/_body 字段 → ApiClient 非 JSON 响应包装，断言需适配
- 断言期望值和实际值只是字段名不同 → 断言字段名不对，不是值的问题

风险评估：
- 401/403 认证失败 → blocker，所有认证用例都会失败
- fixture 链断裂 → high，影响所有依赖该 fixture 的用例
- 单个参数化用例失败 → low，不影响其他用例
- 搜索/查询类接口失败 → low，只读操作
- 创建/删除类接口失败 → high，影响数据状态

输出 JSON：
{
    "final_verdict": "auto_fix | ignore | needs_manual | env_issue | data_issue",
    "risk_level": "blocker | high | medium | low",
    "confidence": "high | medium | low",
    "reasoning": "综合各专家意见的最终判断",
    "fix_suggestion": "修复建议（如果 auto_fix）",
    "agents_agreed": true,
    "agents_disagreed_on": "冲突点（如果有）"
}"""


class Coordinator(BaseAgent):
    def __init__(self):
        super().__init__("Coordinator", SYSTEM_PROMPT)

    def run(self, evidence: dict, opinions: dict) -> dict:
        opinion_text = "\n\n".join(
            f"【{name}】\n{opinion}"
            for name, opinion in opinions.items()
        )

        human = f"""【失败用例】
- 测试: {evidence.get('test_name', '')}
- 接口: {evidence.get('request', {}).get('path', '')}
- HTTP 状态: {evidence.get('response', {}).get('http_status', '')}
- 错误类型: {evidence.get('assertion', {}).get('error_type', '')}

【各专家意见】
{opinion_text}

请综合各专家意见，做出最终判断。"""

        messages = [
            SystemMessage(content=self.system_prompt),
            HumanMessage(content=human),
        ]
        raw = _call_llm_with_retry(self.llm, messages, self.name)
        return _parse_json_response(raw)