import requests


class ApiClient:
    """通用 API 客户端，管理 base_url 和 headers"""

    def __init__(self, base_url: str, headers: dict = None):
        self.base_url = base_url.rstrip("/")
        self.session = requests.Session()
        if headers:
            self.session.headers.update(headers)

    def _parse(self, resp: requests.Response) -> dict:
        try:
            return resp.json()
        except Exception:
            return {"_status": resp.status_code, "_body": resp.text[:200]}

    def post(self, path: str, data: dict = None, **kwargs) -> dict:
        resp = self.session.post(f"{self.base_url}{path}", json=data, **kwargs)
        return self._parse(resp)

    def get(self, path: str, params: dict = None, **kwargs) -> dict:
        resp = self.session.get(f"{self.base_url}{path}", params=params, **kwargs)
        return self._parse(resp)

    def put(self, path: str, data: dict = None, **kwargs) -> dict:
        resp = self.session.put(f"{self.base_url}{path}", json=data, **kwargs)
        return self._parse(resp)

    def delete(self, path: str, **kwargs) -> dict:
        resp = self.session.delete(f"{self.base_url}{path}", **kwargs)
        return self._parse(resp)