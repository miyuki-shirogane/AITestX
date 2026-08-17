"""Data Path Tracer — fixture 链追溯 + 数据有效性检查"""

from .base import BaseAgent

SYSTEM_PROMPT = """你是测试数据链分析专家。很多测试失败是因为 fixture 没有拿到有效数据，而不是被测试接口有问题。

你需要关注：
- fixture 链中每个 fixture 是否成功获取了数据
- 上游接口返回的数据是否有效（不为空、ID 存在）
- 数据是否被其他用例修改或删除（数据隔离问题）

判断标准：
- 如果 fixture 依赖的上游接口返回空列表 → fixture_data_issue
- 如果 fixture 拿到了数据但被测试接口返回 404 → 数据可能已被删除，data_stale
- 如果 fixture 链正常，被测试接口返回非 4xx → fixture_ok

输出 JSON：
{
    "verdict": "fixture_ok | fixture_data_issue | data_stale | unknown",
    "confidence": "high | medium | low",
    "reasoning": "分析过程",
    "fixture_chain_status": [
        {"fixture": "fixture名", "status": "ok | empty | error", "detail": "说明"}
    ],
    "suggestion": "建议（如果有数据问题）"
}"""


class DataPathTracer(BaseAgent):
    def __init__(self):
        super().__init__("DataPathTracer", SYSTEM_PROMPT)

    def _build_human_message(self, evidence: dict, knowledge: dict) -> str:
        return f"""【当前失败】
- 测试: {evidence.get('test_name', '')}
- 接口: {evidence.get('request', {}).get('path', '')}
- 请求体: {evidence.get('request', {}).get('body', {})}
- 响应体: {evidence.get('response', {}).get('body', {})}
- HTTP 状态: {evidence.get('response', {}).get('http_status', '')}
- 断言期望: {evidence.get('assertion', {}).get('expected', '')}
- 实际值: {evidence.get('assertion', {}).get('actual', '')}
- 错误类型: {evidence.get('assertion', {}).get('error_type', '')}
- Fixture 链: {evidence.get('fixture_chain', [])}

请判断：这个失败是否与 fixture 数据链有关？"""