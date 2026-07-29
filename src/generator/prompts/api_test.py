from langchain_core.prompts import ChatPromptTemplate

API_TEST_PROMPT = ChatPromptTemplate.from_messages([
    ("system", "你是一个资深测试工程师，擅长编写pytest测试用例。"),
    ("human", """
请根据以下API文档，生成pytest测试用例。

API文档：
{api_doc}

要求：
1. 每个用例包含清晰的函数名和docstring
2. 使用 hamcrest 的 assert_that 进行断言，不要用原生的 assert
3. import 统一使用 from hamcrest import *
4. 覆盖正常场景和异常场景
5. 直接输出可运行的Python代码，不要解释
    """),
])

API_TEST_RAG_PROMPT = ChatPromptTemplate.from_messages([
    ("system", """你是一个资深测试工程师。
请根据给定的API文档和参考用例，生成pytest测试用例。
严格模仿参考用例的编码风格、命名规范、断言方式。"""),
    ("human", """
## API文档
{api_doc}

## 参考用例（请模仿其风格）
{reference_cases}

## 要求
1. 函数命名遵循 {naming_style} 风格
2. 使用 hamcrest 的 assert_that 进行断言（参考用例中 assert_that 的用法），不要用原生 assert
3. 覆盖正常场景、异常场景、边界值
4. 如果参考用例使用了 @pytest.mark.parametrize、@pytest.fixture、@allure.testcase 等装饰器，请同样使用
5. 如果参考用例使用了 logging.info + pformat 记录请求/响应，请同样使用
6. 直接输出Python代码，不要markdown代码块标记
7. 每个用例包含清晰的docstring
    """),
])