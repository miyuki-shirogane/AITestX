import json
import os
import re
import subprocess
import glob
from dotenv import load_dotenv

load_dotenv()


def analyze_upstream_deps(output_dir: str = "output") -> dict:
    """分析失败用例，找到需要上游数据的参数"""
    deps = {}

    for f in sorted(glob.glob(f"{output_dir}/*.py")):
        with open(f) as fh:
            content = fh.read()

        if "@pytest.mark.skip" in content:
            continue

        # 找到测试中的占位符: "valid_xxx"
        placeholders = re.findall(r'"valid_(\w+)"', content)
        if not placeholders:
            continue

        result = subprocess.run(
            ["pytest", f, "--tb=no", "-q", "--no-header"],
            capture_output=True, text=True, timeout=30
        )
        output = result.stdout + result.stderr
        if "FAILED" not in output:
            continue

        for placeholder in set(placeholders):
            # 提取关键词: valid_design_id → design
            keyword = placeholder.replace("valid_", "").rstrip("_").replace("_id", "")
            if not keyword or len(keyword) < 2:
                continue
            name = f"valid_{keyword}_id"
            if name not in deps:
                deps[name] = {"files": [], "keyword": keyword}
            deps[name]["files"].append(os.path.basename(f))

    return deps


def match_upstream_endpoints(deps: dict, swagger_path: str = "target_service/solgrid-friend-full.json") -> dict:
    """在 Swagger 中匹配能提供上游数据的接口"""
    with open(swagger_path) as f:
        spec = json.load(f)

    for fixture_name, info in deps.items():
        keyword = info["keyword"]
        candidates = []

        for path, methods in spec.get("paths", {}).items():
            for method in ["get", "post"]:
                if method not in methods:
                    continue
                op = methods[method]
                summary = (op.get("summary") or "").lower()
                path_lower = path.lower()

                # 排除自身和 action 类
                action_words = ["create", "delete", "cancel", "accept", "reject", "send", "modify", "remove", "submit"]
                if any(w in path_lower for w in action_words):
                    continue

                score = 0
                if keyword in path_lower:
                    score += 5
                if keyword in summary:
                    score += 3
                # 搜索类接口加分
                if "search" in path_lower or "查询" in summary or "分页" in summary:
                    score += 2

                if score > 0:
                    resp_schema = _get_response_schema(op, spec)
                    has_list = "items" in str(resp_schema).lower() or "array" in str(resp_schema).lower()
                    candidates.append({
                        "path": path,
                        "method": method.upper(),
                        "score": score,
                        "has_list": has_list,
                        "summary": op.get("summary", ""),
                    })

        candidates.sort(key=lambda x: -x["score"])
        if candidates:
            best = candidates[0]
            deps[fixture_name]["endpoint"] = best["path"]
            deps[fixture_name]["method"] = best["method"]
            deps[fixture_name]["has_list"] = best["has_list"]

    return deps


def _get_response_schema(op: dict, spec: dict) -> dict:
    for code, resp in op.get("responses", {}).items():
        if code.startswith("2"):
            content = resp.get("content", {})
            json_content = content.get("application/json", {})
            schema = json_content.get("schema", {})
            if "$ref" in schema:
                ref = schema["$ref"]
                parts = ref.lstrip("#/").split("/")
                resolved = spec
                for part in parts:
                    resolved = resolved.get(part, {})
                return resolved
            return schema
    return {}


def generate_fixtures(deps: dict, output_path: str = "output/conftest.py") -> str:
    lines = [
        '"""Phase 3 自动生成的上游数据 fixture"""',
        'import os',
        'import pytest',
        'from dotenv import load_dotenv',
        'from src.api_client import ApiClient',
        '',
        'load_dotenv()',
        '',
        'BASE_URL = "https://solgrid-friend-api.rivtower.cc"',
        '',
        '@pytest.fixture(scope="session")',
        'def auth_headers():',
        '    client = ApiClient(base_url=BASE_URL)',
        '    resp = client.post("/api/v1/user/login", data={',
        '        "email": os.getenv("TEST_EMAIL"),',
        '        "password": os.getenv("TEST_PASSWORD"),',
        '    })',
        '    return {"Authorization": resp["data"]["accessToken"]}',
        '',
    ]

    for fixture_name, info in deps.items():
        if not info.get("endpoint"):
            lines.append(f"# {fixture_name}: 未找到上游接口")
            lines.append("")
            continue

        endpoint = info["endpoint"]
        method = info.get("method", "GET")
        has_list = info.get("has_list", False)

        lines.append(f'@pytest.fixture(scope="session")')
        lines.append(f'def {fixture_name}(auth_headers):')
        lines.append(f'    """从 {method} {endpoint} 获取真实数据"""')
        lines.append(f'    client = ApiClient(base_url=BASE_URL, headers=auth_headers)')

        if method == "GET":
            lines.append(f'    resp = client.get("{endpoint}")')
        else:
            lines.append(f'    resp = client.post("{endpoint}", data={{}})')

        if has_list:
            lines.append(f'    data = resp.get("data", {{}})')
            lines.append(f'    items = data.get("items", data) if isinstance(data, dict) else data')
            lines.append(f'    if isinstance(items, list) and items:')
            lines.append(f'        first = items[0]')
            lines.append(f'        return first.get("id", first.get("{fixture_name}", str(first)))')
        else:
            lines.append(f'    data = resp.get("data", {{}})')
            lines.append(f'    if isinstance(data, dict):')
            lines.append(f'        return data.get("id", data.get("{fixture_name}", str(data)))')
            lines.append(f'    return str(data) if data else ""')

        lines.append(f'    pytest.skip("无法获取 {fixture_name}")')
        lines.append('')

    content = "\n".join(lines)
    with open(output_path, "w") as f:
        f.write(content)
    return content


def orchestrate(output_dir: str = "output"):
    print("=" * 60)
    print("AITestX Phase 3 - 上游依赖编排")
    print("=" * 60)

    print("\n1. 分析失败的测试用例...")
    deps = analyze_upstream_deps(output_dir)
    if not deps:
        print("   没有发现需要上游数据的用例")
        return
    for name, info in deps.items():
        print(f"   {name}: 关键词={info['keyword']}, {len(info['files'])} 个文件")

    print("\n2. 匹配上游接口...")
    deps = match_upstream_endpoints(deps)
    for name, info in deps.items():
        ep = info.get("endpoint", "未找到")
        print(f"   {name} → {info.get('method', '?')} {ep}")

    print("\n3. 生成 conftest.py...")
    generate_fixtures(deps)
    print(f"   已保存到 {output_dir}/conftest.py")

    print("\n4. 验证...")
    result = subprocess.run(
        ["pytest", output_dir, "-q", "--tb=no"],
        capture_output=True, text=True, timeout=120
    )
    output = result.stdout + result.stderr
    passed = output.count("PASSED")
    failed = output.count("FAILED")
    skipped = output.count("SKIPPED")
    print(f"   通过: {passed}, 失败: {failed}, 跳过: {skipped}")