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
        ("system", """你是一个测试故障分析专家。判断以下测试失败是否应该自动修复断言值。

返回 JSON：
{{
    "can_auto_fix": true/false,
    "fix_description": "如果可以修复，描述怎么改"
}}

判断标准只有一条：
- 测试的**意图**和 API 的**实际行为**是否一致？

具体来说：
- 测试意图是"成功"（函数名含 success、断言 code=0 或 success=True），但 API 返回了 400/404/statusCode 等错误 → **意图和行为不一致，can_auto_fix=false**，说明测试数据有问题，不是断言问题
- 测试意图是"成功"，API 也返回了成功（code=200），只是某个字段值对不上（如 code=0 vs 200）→ **意图和行为一致，can_auto_fix=true**，修断言值
- 测试意图是"失败"（断言 code>0 或 message 包含某错误），API 也返回了失败，只是错误消息不同 → **can_auto_fix=true**，修错误消息
- 测试意图是"失败"，但 API 返回了成功（code=200）→ **can_auto_fix=false**，这是服务行为变化，需要人工确认

简而言之：**先看测试意图和 API 行为是否一致，一致才修，不一致不修。**"""),
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