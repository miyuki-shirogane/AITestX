def pytest_collection_modifyitems(items):
    for item in items:
        item.name = item.name.encode("utf-8").decode("unicode_escape")
        item._nodeid = item.nodeid.encode("utf-8").decode("unicode_escape")

# === Phase 3 自动生成的上游数据 fixture ===
import os
import pytest
from dotenv import load_dotenv
from src.api_client import ApiClient

load_dotenv()

BASE_URL = "https://solgrid-friend-api.rivtower.cc"

@pytest.fixture(scope="session")
def auth_headers():
    client = ApiClient(base_url=BASE_URL)
    resp = client.post("/api/v1/user/login", data={
        "email": os.getenv("TEST_EMAIL"),
        "password": os.getenv("TEST_PASSWORD"),
    })
    return {"Authorization": resp["data"]["accessToken"]}

# valid_token_string: 未找到上游接口，需手动配置

@pytest.fixture(scope="session")
def valid_task_id(auth_headers):
    """从 POST /api/v1/user-agent/space/generation-tasks/status 获取真实数据"""
    client = ApiClient(base_url=BASE_URL, headers=auth_headers)
    resp = client.post("/api/v1/user-agent/space/generation-tasks/status", data={})
    data = resp.get("data", {})
    if isinstance(data, dict):
        return data.get("id", str(data))
    return str(data) if data else ""
    pytest.skip("无法获取 valid_task_id")

# 需要此 fixture 的文件 (2 个):
#   test_POST__api_v1_user-agent_space_generation-tasks_{taskId}_cancel.py
#   test_POST__api_v1_user-agent_space_generation-tasks_{taskId}_cancel.py

@pytest.fixture(scope="session")
def valid_design(auth_headers):
    """从 POST /api/v1/user-agent/space/designs/search 获取真实数据"""
    client = ApiClient(base_url=BASE_URL, headers=auth_headers)
    resp = client.post("/api/v1/user-agent/space/designs/search", data={})
    data = resp.get("data", {})
    if isinstance(data, dict):
        return data.get("id", str(data))
    return str(data) if data else ""
    pytest.skip("无法获取 valid_design")

# 需要此 fixture 的文件 (1 个):
#   test_POST__api_v1_user-agent_space_house-construction.py

@pytest.fixture(scope="session")
def valid_design_id(auth_headers):
    """从 POST /api/v1/user-agent/space/designs/search 获取真实数据"""
    client = ApiClient(base_url=BASE_URL, headers=auth_headers)
    resp = client.post("/api/v1/user-agent/space/designs/search", data={})
    data = resp.get("data", {})
    if isinstance(data, dict):
        return data.get("id", str(data))
    return str(data) if data else ""
    pytest.skip("无法获取 valid_design_id")

# 需要此 fixture 的文件 (1 个):
#   test_POST__api_v1_user-agent_space_room-design.py

@pytest.fixture(scope="session")
def valid_asset_id(auth_headers):
    """从 POST /api/v1/visual-assets/create 获取真实数据"""
    client = ApiClient(base_url=BASE_URL, headers=auth_headers)
    resp = client.post("/api/v1/visual-assets/create", data={})
    data = resp.get("data", {})
    if isinstance(data, dict):
        return data.get("id", str(data))
    return str(data) if data else ""
    pytest.skip("无法获取 valid_asset_id")

# 需要此 fixture 的文件 (1 个):
#   test_POST__api_v1_user-agent_space_room-design.py
