import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate

load_dotenv()


def _get_llm():
    return ChatOpenAI(
        model="deepseek-chat",
        api_key=os.getenv("DEEPSEEK_API_KEY"),
        base_url=os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com"),
        temperature=0,
        timeout=300,
        max_retries=2,
    )


def analyze_failure(test_code: str, test_name: str, error_message: str) -> dict:
    """分析失败原因，返回分类和修复建议"""
    llm = _get_llm()

    prompt = ChatPromptTemplate.from_messages([
        ("system", """你是一个测试故障分析专家。分析以下测试失败，返回 JSON：

{{
    "category": "assertion_mismatch | type_error | import_error | service_bug | upstream_data_needed | unknown",
    "reason": "失败原因的一句话描述",
    "can_auto_fix": true/false,
    "fix_description": "如果可以自动修复，描述修复方案"
}}

分类说明：
- assertion_mismatch: 断言值不对（期望 code=0 实际是 200，期望消息"邮箱不能为空"实际是"用户未找到"等），**默认 can_auto_fix=true**
- type_error: 类型断言错误（期望 instance_of(str) 实际是 dict），**默认 can_auto_fix=true**
- import_error: 缺少 import 语句，**默认 can_auto_fix=true**
- service_bug: 服务端真的出 Bug 了（500 错误等），can_auto_fix=false
- upstream_data_needed: 需要上游接口提供数据，can_auto_fix=false
- unknown: 无法判断，can_auto_fix=false

**重要：只要是断言值对不上、类型对不上、缺少 import，一律标记 can_auto_fix=true**"""),
        ("human", """
测试用例: {test_name}

测试代码:
```python
{test_code}
```

错误信息:
{error}
        """),
    ])

    chain = prompt | llm
    result = chain.invoke({
        "test_name": test_name,
        "test_code": test_code[:3000],
        "error": error_message[:2000],
    })

    import json
    try:
        content = result.content.strip()
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0]
        elif "```" in content:
            content = content.split("```")[1].split("```")[0]
        return json.loads(content)
    except (json.JSONDecodeError, IndexError):
        return {
            "category": "unknown",
            "reason": result.content[:200],
            "can_auto_fix": False,
            "fix_description": ""
        }


def attempt_fix(test_code: str, test_name: str, error_message: str, analysis: dict) -> str:
    """尝试自动修复测试用例"""
    if not analysis.get("can_auto_fix"):
        return None

    llm = _get_llm()

    prompt = ChatPromptTemplate.from_messages([
        ("system", """你是一个测试代码修复专家。请根据实际错误信息修复测试用例。

修复规则：
1. 只修改断言值和断言逻辑，不要改变测试逻辑
2. 如果实际 code=200 但断言 code=0，改成 code=200
3. 如果实际 data 是 dict 但断言 instance_of(str)，改成验证 dict 字段
4. 如果实际错误消息是"用户未找到"但断言"邮箱不能为空"，改成实际消息
5. 保持原有代码风格、import、装饰器不变
6. 直接输出修复后的完整代码，不要解释
7. 不要用 markdown 代码块包裹
        """),
        ("human", """
测试用例: {test_name}

原始代码:
```python
{test_code}
```

错误信息:
{error}

修复方案: {fix_description}

请输出修复后的完整代码:
        """),
    ])

    chain = prompt | llm
    result = chain.invoke({
        "test_name": test_name,
        "test_code": test_code,
        "error": error_message[:2000],
        "fix_description": analysis.get("fix_description", ""),
    })

    content = result.content.strip()
    if content.startswith("```"):
        content = "\n".join(content.split("\n")[1:-1])
    return content