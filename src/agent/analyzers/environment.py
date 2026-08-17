"""Environment Checker — 区分代码问题 vs 环境抖动"""

from .base import BaseAgent

SYSTEM_PROMPT = """你是环境诊断专家。你区分失败是代码/断言问题还是环境问题。

环境问题特征：
- ConnectionRefused / ConnectionReset / MaxRetries → 网络问题
- 503 Service Unavailable → 服务暂时不可用
- 429 Too Many Requests → 限流
- timeout → 网络或服务响应慢
- 同一个用例之前通过过，现在失败 → 可能是偶发问题

非环境问题特征：
- AssertionError → 断言问题
- KeyError / TypeError → 代码问题
- 400 / 404 / 409 → 业务逻辑问题

输出 JSON：
{
    "verdict": "not_env | flaky | env_down",
    "confidence": "high | medium | low",
    "reasoning": "判断过程",
    "retry_recommended": false
}"""


class EnvironmentChecker(BaseAgent):
    def __init__(self):
        super().__init__("EnvironmentChecker", SYSTEM_PROMPT)

    def _build_human_message(self, evidence: dict, knowledge: dict) -> str:
        return f"""【当前失败】
- 测试: {evidence.get('test_name', '')}
- 接口: {evidence.get('request', {}).get('path', '')}
- 响应体: {evidence.get('response', {}).get('body', {})}
- HTTP 状态: {evidence.get('response', {}).get('http_status', '')}
- 错误类型: {evidence.get('assertion', {}).get('error_type', '')}

请判断：这是环境问题还是代码/断言问题？"""