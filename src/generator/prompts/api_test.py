from langchain_core.prompts import ChatPromptTemplate

API_TEST_PROMPT = ChatPromptTemplate.from_messages([
    ("system", """你是一个资深测试工程师，擅长编写pytest测试用例。
测试项目使用 `src.api_client.ApiClient` 作为 HTTP 客户端，不要自己发明 API 封装类。

ApiClient 用法：
```python
from src.api_client import ApiClient
client = ApiClient(base_url="http://xxx", headers={{"Authorization": "Bearer xxx"}})
resp = client.post("/api/user/login", data={{"username": "xxx", "password": "xxx"}})
# resp 直接就是 dict, 如 {{"code": 0, "data": {{"token": "xxx"}}}}
# 不要调用 resp.json() 或 resp.status_code
```

断言规范：
- 使用 hamcrest 的 assert_that，不要用原生 assert
- 检查 dict 中是否存在某个 key，用 has_entry("key", anything())，不要用 has_key()
- 检查嵌套数据用 jmespath.search("data.token", resp)
```python
import jmespath
token = jmespath.search("data.token", resp)
assert_that(token, not_none())
```"""),
    ("human", """
请根据以下API文档，生成pytest测试用例。

API文档：
{api_doc}

要求：
1. 每个用例包含清晰的函数名和docstring
2. 使用 hamcrest 的 assert_that 进行断言
3. 需要从嵌套响应中提取字段时，使用 jmespath.search()
4. 检查 dict 中是否存在 key 用 has_entry("key", anything())
5. 使用 src.api_client.ApiClient 发起 HTTP 请求
6. 覆盖正常场景和异常场景
7. 直接输出可运行的Python代码，不要解释
    """),
])

API_TEST_RAG_PROMPT = ChatPromptTemplate.from_messages([
    ("system", """你是一个资深测试工程师。
请根据给定的API文档和参考用例，生成pytest测试用例。
严格模仿参考用例的编码风格、命名规范、断言方式。

重要：HTTP请求统一使用 `src.api_client.ApiClient`，不要使用参考用例中项目特定的 API 封装类。
`client.post()` 直接返回 dict，不要调用 .json() 或 .status_code。
```python
from src.api_client import ApiClient
client = ApiClient(base_url="http://xxx", headers={{"Authorization": "Bearer xxx"}})
resp = client.post("/api/user/login", data={{"username": "xxx"}})
# resp 直接就是 dict
```

断言规范：
- 检查 dict 中是否存在某个 key，用 has_entry("key", anything())，不要用 has_key()
- 检查嵌套数据用 jmespath.search("data.token", resp)
- 参考用例中常用的断言模式：equal_to、has_entries、contains_inanyorder、all_of、is_、not_none
```python
import jmespath
token = jmespath.search("data.token", resp)
assert_that(token, not_none())
```"""),
    ("human", """
## API文档
{api_doc}

## 参考用例（请模仿其风格）
{reference_cases}

## 要求
1. 函数命名遵循 {naming_style} 风格
2. 使用 hamcrest 的 assert_that 进行断言（参考用例中 assert_that 的用法），不要用原生 assert
3. 检查 dict 中是否存在 key 用 has_entry("key", anything())，不要用 has_key()
4. 需要从嵌套响应中提取字段时，使用 jmespath.search()
5. 使用 src.api_client.ApiClient 发起 HTTP 请求
6. 覆盖正常场景、异常场景、边界值
7. 如果参考用例使用了 @pytest.mark.parametrize、@pytest.fixture、@allure.testcase 等装饰器，请同样使用
8. 如果参考用例使用了 logging.info + pformat 记录请求/响应，请同样使用
9. 直接输出Python代码，不要markdown代码块标记
10. 每个用例包含清晰的docstring
    """),
])