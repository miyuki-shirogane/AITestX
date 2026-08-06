from langchain_core.prompts import ChatPromptTemplate

API_TEST_PROMPT = ChatPromptTemplate.from_messages([
    ("system", """你是一个资深测试工程师，擅长编写pytest测试用例。
测试项目使用 `src.api_client.ApiClient` 作为 HTTP 客户端，不要自己发明 API 封装类。

认证方式：如果接口需要认证，用 fixture 自动登录获取 token，不要用 skipif 或从环境变量读 token。
```python
from src.api_client import ApiClient
import os, pytest

@pytest.fixture(scope="session")
def auth_headers():
    client = ApiClient(base_url="http://xxx")
    resp = client.post("/api/v1/user/login", data={{"email": os.getenv("TEST_EMAIL"), "password": os.getenv("TEST_PASSWORD")}})
    token = resp["data"]["accessToken"]
    return {{"Authorization": token}}  # token 已包含 Bearer 前缀，不要加 f"Bearer {{token}}"

def test_xxx(auth_headers):
    client = ApiClient(base_url="http://xxx", headers=auth_headers)
    resp = client.post("/api/xxx")
    # resp 直接就是 dict, 不要调用 resp.json() 或 resp.status_code
```

断言规范：
- 检查 dict 的 key-value 用 has_entries({{"code": 0}})，等值比较直接传值，不要包 equal_to()
- 只在不等于/大于/包含等复杂匹配时才用显式 matcher: has_entries({{"code": greater_than(0)}})
- 检查 dict 中是否存在某个 key 用 has_entries({{"code": anything()}})
- 检查嵌套数据用 jmespath.search("data.token", resp)
- **重要：如果 API 文档的响应示例中 data 字段有子结构（如 {{"token": "xxx", "user_id": 123}}），必须对每个子字段做类型和值的断言，不要只验 not_none()**
```python
import jmespath
assert_that(resp, has_entries({{"code": 0}}))
token = jmespath.search("data.token", resp)
assert_that(token, instance_of(str))
assert_that(token, is_not(empty()))
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
6. 如果接口需要认证，用 fixture 自动登录获取 token，不要用 skipif 或环境变量
7. 覆盖正常场景和异常场景
8. 直接输出可运行的Python代码，不要解释
    """),
])

API_TEST_RAG_PROMPT = ChatPromptTemplate.from_messages([
    ("system", """你是一个资深测试工程师。
请根据给定的API文档和参考用例，生成pytest测试用例。
严格模仿参考用例的编码风格、命名规范、断言方式。

重要：HTTP请求统一使用 `src.api_client.ApiClient`，不要使用参考用例中项目特定的 API 封装类。
`client.post()` 直接返回 dict，不要调用 .json() 或 .status_code。
如果接口需要认证，用 fixture 自动登录获取 token，不要用 skipif 或从环境变量读 token。
```python
from src.api_client import ApiClient
import os, pytest

@pytest.fixture(scope="session")
def auth_headers():
    client = ApiClient(base_url="http://xxx")
    resp = client.post("/api/v1/user/login", data={{"email": os.getenv("TEST_EMAIL"), "password": os.getenv("TEST_PASSWORD")}})
    token = resp["data"]["accessToken"]
    return {{"Authorization": token}}  # token 已包含 Bearer 前缀，不要加 f"Bearer {{token}}"
```

断言规范：
- 检查 dict 的 key-value 用 has_entries({{"code": 0}})，等值比较直接传值，不要包 equal_to()
- 复杂匹配时才用显式 matcher: has_entries({{"code": greater_than(0)}})
- 检查 dict 中是否存在某个 key 用 has_entries({{"code": anything()}})
- 检查嵌套数据用 jmespath.search("data.token", resp)
- **重要：如果 API 文档的响应示例中 data 字段有子结构，必须对每个子字段做类型和值的断言**
- 参考用例中常用：equal_to、has_entries、contains_inanyorder、all_of、is_、not_none、instance_of、is_not
```python
import jmespath
token = jmespath.search("data.token", resp)
assert_that(token, instance_of(str))
assert_that(token, is_not(empty()))
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
6. 如果接口需要认证，用 fixture 自动登录获取 token，不要用 skipif 或环境变量
7. 覆盖正常场景、异常场景、边界值
8. 如果参考用例使用了 @pytest.mark.parametrize、@pytest.fixture、@allure.testcase 等装饰器，请同样使用
9. 如果参考用例使用了 logging.info + pformat 记录请求/响应，请同样使用
10. 直接输出Python代码，不要markdown代码块标记
11. 每个用例包含清晰的docstring
    """),
])