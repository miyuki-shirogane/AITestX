"""Contract Analyst — 断言 vs API 契约 vs 实际响应 三方对比"""

from .base import BaseAgent

SYSTEM_PROMPT = """你是 API 契约分析师。你对比测试断言、API 实际响应、Swagger 文档三者，找出不一致的地方。

你特别警惕 AI 生成测试代码的常见缺陷：
- 「对称性假设」：AI 假设请求参数和响应字段有对称关系，但实际 API 往往不对称
- 「枚举全量假设」：AI 把 Swagger 中所有枚举值都当成合法值，但实际 API 可能只接受部分
- 「字段名猜测」：AI 在文档不明确时猜测字段名（如 code vs statusCode）
- 「错误响应格式假设」：AI 假设所有错误响应都有 JSON body，但 401/403 可能没有
- 「分页硬编码假设」：AI 假设分页参数一定原样返回

对比逻辑：
1. 断言期望什么？
2. API 实际返回了什么？
3. Swagger 文档定义了什么？
4. 三者中哪两个不一致？

输出 JSON：
{
    "verdict": "assertion_fix | schema_change | potential_bug | consistent",
    "generated_code_flaw": "对称性假设 | 枚举全量假设 | 字段名猜测 | 错误响应格式假设 | 分页硬编码假设 | null",
    "confidence": "high | medium | low",
    "reasoning": "分析过程",
    "fix_suggestion": "修复建议（如果 assertion_fix）",
    "comparison": {
        "assertion": "断言期望什么",
        "api_response": "API 实际返回什么",
        "swagger": "Swagger 文档定义什么"
    }
}"""


class ContractAnalyst(BaseAgent):
    def __init__(self):
        super().__init__("ContractAnalyst", SYSTEM_PROMPT)

    def _retrieve_knowledge(self, evidence: dict) -> dict:
        knowledge = super()._retrieve_knowledge(evidence)
        api_path = evidence.get("request", {}).get("path", "")
        knowledge["api_doc"] = _load_api_doc(api_path)
        return knowledge

    def _build_human_message(self, evidence: dict, knowledge: dict) -> str:
        return f"""【Swagger 文档】
{knowledge.get('api_doc', '（未找到对应文档）')}

【当前失败】
- 测试: {evidence.get('test_name', '')}
- 接口: {evidence.get('request', {}).get('path', '')}
- 请求体: {evidence.get('request', {}).get('body', {})}
- 响应体: {evidence.get('response', {}).get('body', {})}
- HTTP 状态: {evidence.get('response', {}).get('http_status', '')}
- 断言期望: {evidence.get('assertion', {}).get('expected', '')}
- 实际值: {evidence.get('assertion', {}).get('actual', '')}
- 错误类型: {evidence.get('assertion', {}).get('error_type', '')}

请对比断言、API 实际响应、Swagger 文档，找出不一致的地方。"""


def _load_api_doc(api_path: str) -> str:
    import os
    safe_name = api_path.replace(" ", "_").replace("/", "_").replace("-", "_").replace("{", "_").replace("}", "_").strip("_")
    doc_path = f"target_service/api/{safe_name}.md"
    if os.path.exists(doc_path):
        with open(doc_path, encoding="utf-8") as f:
            return f.read()
    return ""