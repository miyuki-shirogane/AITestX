import logging
from pprint import pformat

import allure
import pytest
from hamcrest import *
from src.api_client import ApiClient


client = ApiClient(base_url="http://localhost:8080")


@pytest.mark.SingleAPI
@allure.feature("参数校验")
@pytest.mark.parametrize(
    "field, value, expected_msg",
    [
        ("name", "", "名称不能为空"),
        ("name", "a" * 101, "名称不能超过100字符"),
        ("email", "not-an-email", "邮箱格式不正确"),
        ("age", -1, "年龄不能为负数"),
        ("age", "abc", "年龄必须为整数"),
    ],
    ids=["名称为空", "名称超长", "邮箱格式错误", "年龄负数", "年龄非数字"]
)
def test_field_validation(field, value, expected_msg):
    """参数校验：非法值应返回明确错误提示"""
    data = {field: value}
    logging.info(f"请求: {pformat(data)}")
    resp = client.post("/api/resource", data=data)
    logging.info(f"响应: {pformat(resp)}")
    assert_that(resp, has_entries({"code": greater_than(0)}))
    assert_that(resp["msg"], contains_string(expected_msg))


@pytest.mark.SingleAPI
@allure.feature("幂等性")
def test_idempotency():
    """重复提交相同请求，结果一致"""
    data = {"name": "test", "email": "test@example.com"}
    resp1 = client.post("/api/resource", data=data)
    resp2 = client.post("/api/resource", data=data)
    assert_that(resp1["code"], equal_to(resp2["code"]))
    assert_that(resp1["msg"], equal_to(resp2["msg"]))