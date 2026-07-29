import requests
import json


class ApiClient:
    """通用 API 客户端，管理 base_url 和 headers"""

    def __init__(self, base_url: str, headers: dict = None):
        self.base_url = base_url.rstrip("/")
        self.session = requests.Session()
        self.session.headers.update(headers or {})
        self.session.headers.setdefault("Content-Type", "application/json")

    def post(self, path: str, data: dict = None, **kwargs) -> dict:
        resp = self.session.post(f"{self.base_url}{path}", json=data, **kwargs)
        return resp.json()

    def get(self, path: str, **kwargs) -> dict:
        resp = self.session.get(f"{self.base_url}{path}", **kwargs)
        return resp.json()

    def put(self, path: str, data: dict = None, **kwargs) -> dict:
        resp = self.session.put(f"{self.base_url}{path}", json=data, **kwargs)
        return resp.json()

    def delete(self, path: str, **kwargs) -> dict:
        resp = self.session.delete(f"{self.base_url}{path}", **kwargs)
        return resp.json()