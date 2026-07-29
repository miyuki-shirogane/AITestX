from langchain_core.prompts import ChatPromptTemplate

BOUNDARY_TEST_PROMPT = ChatPromptTemplate.from_messages([
    ("system", "你是一个边界值测试专家。"),
    ("human", """
请为以下API生成边界值测试用例，覆盖：
- 最小值、最大值
- 刚好超出边界
- 空值、null
- 超长字符串

API文档：
{api_doc}

直接输出可运行的pytest代码。
    """),
])