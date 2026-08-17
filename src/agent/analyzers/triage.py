"""Triage Specialist — 失败模式识别 + 排查策略"""

from .base import BaseAgent, _load_testing_heuristics

SYSTEM_PROMPT = """你是资深测试排查专家。你经手过大量自动化测试失败案例，能根据错误模式快速判断最可能的原因和排查路径。

你的专业经验：
- KeyError 且响应体有 _status/_body → ApiClient 对非 JSON 响应做了包装，断言用错了字段
- parametrized 用例中部分通过部分失败 → 失败的参数组合通常是 API 不支持的边界值
- 同一字段在多次修复中来回修改 → 断言陷入振荡，需要自适应断言
- AssertionError 且期望值和实际值只是字段名不同 → 断言字段名不对，不是值的问题
- 响应体是空字符串或非 JSON → 接口可能返回了非标准格式

排查优先级：
1. 先看响应体结构是否正确（是不是 JSON，有没有 code 字段）
2. 再看断言期望值和实际值的差异是字段名还是值
3. 最后判断是否属于已知的 AI 生成代码缺陷

输出 JSON：
{
    "most_likely_cause": "最可能的原因（1-2句话）",
    "category": "assertion_mismatch | fixture_data_issue | generated_code_flaw | api_behavior_change | environment_issue",
    "confidence": "high | medium | low",
    "triage_steps": ["排查步骤1", "排查步骤2"],
    "is_flaky": false
}"""


class TriageSpecialist(BaseAgent):
    def __init__(self):
        super().__init__("TriageSpecialist", SYSTEM_PROMPT)

    def _build_human_message(self, evidence: dict, knowledge: dict) -> str:
        heuristics = _load_testing_heuristics()
        heuristics_text = "\n".join(
            f"- {h.get('pattern', '')}: {h.get('cause', '')}"
            for h in heuristics
        ) if heuristics else "（无）"

        concepts = knowledge.get("concepts", [])
        concepts_text = "\n".join(
            f"- {c.get('name', '')}: {c.get('knowledge', '')}"
            for c in concepts
        ) if concepts else "（无）"

        return f"""【已知测试经验 — 错误模式排查】
{heuristics_text}

【业务知识 — 相关概念】
{concepts_text}

【当前失败】
- 测试: {evidence.get('test_name', '')}
- 接口: {evidence.get('request', {}).get('path', '')}
- 请求体: {evidence.get('request', {}).get('body', {})}
- 响应体: {evidence.get('response', {}).get('body', {})}
- HTTP 状态: {evidence.get('response', {}).get('http_status', '')}
- 断言期望: {evidence.get('assertion', {}).get('expected', '')}
- 实际值: {evidence.get('assertion', {}).get('actual', '')}
- 错误类型: {evidence.get('assertion', {}).get('error_type', '')}
- Fixture 链: {evidence.get('fixture_chain', [])}

请根据错误模式判断最可能的原因和排查路径。"""