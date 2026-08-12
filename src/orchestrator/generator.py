import os


def generate(deps: list[dict], config: dict, output_dir: str = "output") -> str:
    """生成 output/conftest.py，pytest 会自动继承根 conftest.py"""
    import json
    base_url = config.get("base_url", "http://localhost:8080")
    auth_url = config.get("auth_url", "/api/v1/user/login")
    auth_body = config.get("auth_body", '{"email": "test@example.com", "password": "test"}')
    token_path = config.get("token_path", "data.accessToken")

    lines = [
        "# === Phase 3 自动生成的上游数据 fixture ===",
        'import os',
        'import json',
        'import pytest',
        'from dotenv import load_dotenv',
        'from src.api_client import ApiClient',
        '',
        'load_dotenv()',
        '',
        f'BASE_URL = "{base_url}"',
        '',
        '@pytest.fixture(scope="session")',
        'def auth_headers():',
        '    client = ApiClient(base_url=BASE_URL)',
        f'    auth_body = json.loads(os.getenv("AUTH_BODY", \'{auth_body}\'))',
        f'    resp = client.post(os.getenv("AUTH_URL", "{auth_url}"), data=auth_body)',
        f'    token_path = os.getenv("AUTH_TOKEN_PATH", "{token_path}").split(".")',
        '    token = resp',
        '    for key in token_path:',
        '        token = token[key]',
        '    return {"Authorization": token}',
        '',
    ]

    for dep in deps:
        best = dep.get("candidates", [None])[0] if dep.get("candidates") else None
        if not best:
            lines.append(f"# {dep['placeholder']}: 未找到上游接口，需手动配置")
            lines.append("")
            continue

        lines.append(f'@pytest.fixture(scope="session")')
        lines.append(f'def {dep["placeholder"]}(auth_headers):')
        lines.append(f'    """从 {best["method"]} {best["path"]} 获取真实数据"""')
        lines.append(f'    client = ApiClient(base_url=BASE_URL, headers=auth_headers)')

        if best["method"] == "GET":
            lines.append(f'    resp = client.get("{best["path"]}")')
        else:
            lines.append(f'    resp = client.post("{best["path"]}", data={{}})')

        if best.get("has_list"):
            lines.append(f'    data = resp.get("data", {{}})')
            lines.append(f'    items = data.get("items", data) if isinstance(data, dict) else data')
            lines.append(f'    if isinstance(items, list) and items:')
            lines.append(f'        return items[0].get("id", str(items[0]))')
        else:
            lines.append(f'    data = resp.get("data", {{}})')
            lines.append(f'    if isinstance(data, dict):')
            lines.append(f'        return data.get("id", str(data))')
            lines.append(f'    return str(data) if data else ""')

        lines.append(f'    pytest.skip("无法获取 {dep["placeholder"]}")')
        lines.append('')

        files = dep.get("files", [])
        lines.append(f"# 需要此 fixture 的文件 ({len(files)} 个):")
        for f in files:
            lines.append(f"#   {f}")
        lines.append("")

    content = "\n".join(lines)
    os.makedirs(output_dir, exist_ok=True)
    output_path = f"{output_dir}/conftest.py"
    with open(output_path, "w") as f:
        f.write(content)
    return content