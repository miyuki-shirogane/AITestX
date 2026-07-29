from langchain.prompts import ChatPromptTemplate

EXCEPTION_TEST_PROMPT = ChatPromptTemplate.from_messages([
    ("system", "你是一个异常场景测试专家。"),
    ("human", """
请为以下API生成异常场景测试用例，覆盖：
- 参数类型错误
- 必填参数缺失
- 权限不足
- 并发冲突
- 依赖服务不可用

API文档：
{api_doc}

直接输出可运行的pytest代码。
    """),
])