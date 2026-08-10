from langchain_core.prompts import ChatPromptTemplate

API_TEST_PROMPT = ChatPromptTemplate.from_messages([
    ("system", """你是一个资深测试工程师，擅长编写pytest测试用例。

代码规范（必须严格遵守）：
1. 模块级定义 client = ApiClient(base_url="https://实际地址")
2. 认证接口用 @pytest.fixture(scope="session") 自动登录，返回 {{"Authorization": token}}
3. 需要认证的测试传 headers=auth_headers，不需要的只传 data/params
4. 不要创建额外的 client fixture，直接用模块级的 client
5. GET 请求用 params= 传查询参数；POST 用 data= 传请求体
6. 必须 import 所有使用的库：os, pytest, allure, jmespath, logging 等

```python
# === 以下 import 必须完整，一个都不能少 ===
import os
import pytest
import allure
import logging
import jmespath
from pprint import pformat
from hamcrest import *
from src.api_client import ApiClient

client = ApiClient(base_url="https://api.example.com")

@pytest.fixture(scope="session")
def auth_headers():
    resp = client.post("/api/v1/user/login", data={{"email": os.getenv("TEST_EMAIL"), "password": os.getenv("TEST_PASSWORD")}})
    return {{"Authorization": resp["data"]["accessToken"]}}  # token 已含 Bearer 前缀

def test_public_api():
    resp = client.get("/api/public")
    assert_that(resp, has_entries({{"code": 0}}))

def test_auth_api(auth_headers):
    resp = client.post("/api/private", headers=auth_headers)
    assert_that(resp, has_entries({{"code": 0}}))
```

**重要规则**：
- 测试数据中的业务 ID（如 designId、fileId、locationId）直接用占位字符串，如 `"valid_design_id"`，不要用 `os.getenv("TEST_XXX_ID")`
- 环境变量只用于认证（TEST_EMAIL、TEST_PASSWORD），不用于业务数据
- 业务 ID 由 Phase 3 编排器自动替换为真实值
```"""),
    ("human", """
请根据以下API文档，生成pytest测试用例。

API文档：
{api_doc}

要求：
1. 模块级定义 client = ApiClient(base_url="https://实际地址")
2. 认证用 @pytest.fixture(scope="session") def auth_headers()
3. 不要创建额外的 client fixture
4. 使用 hamcrest assert_that 断言
5. 覆盖正常场景和异常场景
6. 直接输出可运行的Python代码，不要解释
    """),
])

API_TEST_RAG_PROMPT = ChatPromptTemplate.from_messages([
    ("system", """你是一个资深测试工程师。
请根据给定的API文档和参考用例，生成pytest测试用例。
严格模仿参考用例的编码风格、命名规范、断言方式。

代码规范（必须严格遵守）：
1. 模块级定义 client = ApiClient(base_url="https://实际地址")
2. 认证用 @pytest.fixture(scope="session") def auth_headers()
3. 不要创建额外的 client fixture，直接用模块级 client
4. GET 用 params=，POST 用 data=
5. 必须 import 所有使用的库：os, pytest, allure, jmespath, logging, hamcrest

```python
from src.api_client import ApiClient
import os, pytest, allure, logging, jmespath
from pprint import pformat
from hamcrest import *

client = ApiClient(base_url="https://api.example.com")

@pytest.fixture(scope="session")
def auth_headers():
    resp = client.post("/api/v1/user/login", data={{"email": os.getenv("TEST_EMAIL"), "password": os.getenv("TEST_PASSWORD")}})
    return {{"Authorization": resp["data"]["accessToken"]}}
```"""),
    ("human", """
## API文档
{api_doc}

## 参考用例（请模仿其风格）
{reference_cases}

## 要求
1. 函数命名遵循 {naming_style} 风格
2. 使用 hamcrest 的 assert_that 进行断言
3. 模块级定义 client，不要创建额外的 client fixture
4. 认证用 @pytest.fixture(scope="session") def auth_headers()
5. 使用 src.api_client.ApiClient 发起 HTTP 请求
6. 覆盖正常场景、异常场景、边界值
7. 直接输出Python代码，不要markdown代码块标记
8. 每个用例包含清晰的docstring
    """),
])