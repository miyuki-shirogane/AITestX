import os
import time
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate

load_dotenv()

MAX_RETRIES = 3
RETRY_DELAY = 60


def _get_llm():
    return ChatOpenAI(
        model="deepseek-chat",
        api_key=os.getenv("DEEPSEEK_API_KEY"),
        base_url=os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com"),
        temperature=0,
        timeout=300,
        max_retries=2,
    )


def _call_llm_with_retry(chain, inputs: dict, step_name: str) -> str:
    for attempt in range(MAX_RETRIES):
        try:
            result = chain.invoke(inputs)
            return result.content
        except Exception as e:
            msg = str(e)
            if "520" in msg or "429" in msg or "insufficient_quota" in msg:
                if attempt < MAX_RETRIES - 1:
                    delay = RETRY_DELAY * (attempt + 1)
                    print(f"      ⏳ {step_name} API {msg[:50]}... {delay}s后重试({attempt+1}/{MAX_RETRIES})")
                    time.sleep(delay)
                    continue
            raise


def analyze_failure(test_code: str, test_name: str, error_message: str) -> dict:
    """分析失败原因，返回分类和修复建议"""
    llm = _get_llm()

    prompt = ChatPromptTemplate.from_messages([
        ("system", """你是一个测试故障分析专家。分析以下测试失败，返回 JSON：

{{
    "category": "assertion_mismatch | type_error | import_error | invalid_test_data | service_bug | upstream_data_needed | unknown",
    "reason": "失败原因的一句话描述",
    "can_auto_fix": true/false,
    "fix_description": "如果可以自动修复，描述具体修复方案"
}}

分类说明：
- assertion_mismatch: 断言值不对（期望 code=0 实际是 200），**can_auto_fix=true**。但注意：如果测试预期成功(code=0)却返回了400/404等错误码，说明测试数据有问题，应归类为 invalid_test_data
- type_error: 类型断言错误（期望 str 实际是 dict），**can_auto_fix=true**
- import_error: 缺少 import，**can_auto_fix=true**
- invalid_test_data: 测试用的假数据（fileId="valid_file_id"）导致API返回校验错误(400/404)，**can_auto_fix=false**，这不是断言问题，是测试数据需要替换为真实值
- service_bug: 服务端500错误，can_auto_fix=false
- upstream_data_needed: 需要上游接口提供数据（如 location_id），can_auto_fix=false
- unknown: 仅在完全无法判断时使用，can_auto_fix=false

**关键规则：如果测试预期成功(code=0/success=True)但实际返回了400/404/statusCode等校验错误，说明测试数据无效，归类为 invalid_test_data，can_auto_fix=false**"""),
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
    result_text = _call_llm_with_retry(chain, {
        "test_name": test_name,
        "test_code": test_code[:3000],
        "error": error_message[:2000],
    }, "分析失败")

    import json
    try:
        content = result_text.strip()
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0]
        elif "```" in content:
            content = content.split("```")[1].split("```")[0]
        return json.loads(content)
    except (json.JSONDecodeError, IndexError):
        return {
            "category": "unknown",
            "reason": result_text[:200],
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
    result_text = _call_llm_with_retry(chain, {
        "test_name": test_name,
        "test_code": test_code,
        "error": error_message[:2000],
        "fix_description": analysis.get("fix_description", ""),
    }, "修复代码")

    content = result_text.strip()
    if content.startswith("```"):
        content = "\n".join(content.split("\n")[1:-1])
    return content