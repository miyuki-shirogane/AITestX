import json
import re


def analyze(swagger_path: str) -> list[dict]:
    """分析 Swagger 接口的上下游依赖关系

    返回: [{
        "path": "DELETE /designs/{designId}",
        "params": [{"name": "designId", "upstream": "POST /designs/search"}],
        "needs_auth": true
    }, ...]
    """
    with open(swagger_path) as f:
        spec = json.load(f)

    # 先建立索引：哪些接口返回什么
    providers = _build_provider_index(spec)

    results = []
    for path, methods in spec.get("paths", {}).items():
        for method in ["get", "post", "put", "delete", "patch"]:
            if method not in methods:
                continue
            op = methods[method]
            needs_auth = "security" in op

            params = []
            # 提取路径参数
            for p in re.findall(r'\{(\w+)\}', path):
                keyword = _extract_keyword(p)
                upstream = _find_provider(keyword, providers, path)
                params.append({
                    "name": p,
                    "keyword": keyword,
                    "upstream": upstream,
                })

            # 提取请求体参数（带 Id 后缀的字段）
            body_params = _extract_body_params(op, spec)
            for p in body_params:
                keyword = _extract_keyword(p)
                upstream = _find_provider(keyword, providers, path)
                params.append({
                    "name": p,
                    "keyword": keyword,
                    "upstream": upstream,
                })

            results.append({
                "path": f"{method.upper()} {path}",
                "tag": (op.get("tags") or ["未分类"])[0],
                "summary": op.get("summary", ""),
                "needs_auth": needs_auth,
                "params": params,
            })

    return results


def _build_provider_index(spec: dict) -> dict:
    """建立关键词到提供者接口的索引"""
    providers = {}
    action_words = ["delete", "cancel", "accept", "reject", "remove", "submit"]

    for path, methods in spec.get("paths", {}).items():
        path_lower = path.lower()
        # 排除 action 类接口
        if any(w in path_lower for w in action_words):
            continue

        for method in ["get", "post"]:
            if method not in methods:
                continue
            op = methods[method]

            # 检查响应是否包含 id 或 token 字段
            has_id = _response_has_id(op, spec) or _response_has_token(op, spec)
            has_list = _response_has_list(op, spec)

            if not (has_id or has_list):
                continue

            # 提取该接口的关键词
            keywords = _extract_keywords_from_path(path)
            for kw in keywords:
                if kw not in providers:
                    providers[kw] = []
                providers[kw].append({
                    "path": f"{method.upper()} {path}",
                    "has_list": has_list,
                    "summary": op.get("summary", ""),
                })

    return providers


def _extract_body_params(op: dict, spec: dict) -> list[str]:
    """从请求体提取需要上游数据的字段（Id、Token、Key 等后缀）"""
    params = []
    req_body = op.get("requestBody", {})
    content = req_body.get("content", {}).get("application/json", {})
    schema = content.get("schema", {})
    schema = _resolve_ref(schema, spec)
    for prop_name, prop_schema in schema.get("properties", {}).items():
        name_lower = prop_name.lower()
        # Id 后缀或 Token/Key 等需要上游提供的字段
        if name_lower.endswith(("id", "token", "key", "code")):
            # 排除简单类型（如 email、password 等）
            if prop_schema.get("type") == "string" and "format" not in str(prop_schema):
                params.append(prop_name)
    return params


def _extract_keyword(param_name: str) -> str:
    """从参数名提取关键词：designId → design, npcAgentId → npc, visualAssetId → asset"""
    name = param_name.lower()
    # 去掉 Id 后缀
    if name.endswith("id"):
        name = name[:-2]
    # 只取第一个有意义的词
    for word in ["npc", "friend", "design", "task", "location", "asset", "photo", "agent", "proposal", "token"]:
        if word in name:
            return word
    return name


def _extract_keywords_from_path(path: str) -> list[str]:
    """从路径提取关键词：/api/v1/user-agent/space/generation-tasks → [generation, task, tasks, space]"""
    parts = path.lower().split("/")
    keywords = []
    for part in parts[-3:]:
        if part in ("api", "v1", ""):
            continue
        # 去掉复数
        singular = part.rstrip("s")
        keywords.append(singular)
        keywords.append(part)
        # 复合词拆分：generation-tasks → task, generation-task → task
        for sub in part.split("-"):
            sub_singular = sub.rstrip("s")
            if sub_singular not in keywords:
                keywords.append(sub_singular)
            if sub not in keywords:
                keywords.append(sub)
    return keywords


def _find_provider(keyword: str, providers: dict, exclude_path: str) -> dict:
    """为关键词找到上游提供者，优先 search 接口"""
    candidates = providers.get(keyword, [])
    # 排除自身（路径部分匹配）
    candidates = [c for c in candidates if exclude_path not in c["path"]]
    if not candidates:
        return None

    # 优先 search
    search_candidates = [c for c in candidates if "search" in c["path"].lower()]
    if search_candidates:
        return search_candidates[0]

    # 其次列表型
    list_candidates = [c for c in candidates if c["has_list"]]
    if list_candidates:
        # 优先最短路径（最通用）
        list_candidates.sort(key=lambda c: len(c["path"]))
        return list_candidates[0]

    return candidates[0]


def _response_has_id(op: dict, spec: dict) -> bool:
    for code, resp in op.get("responses", {}).items():
        if not code.startswith("2"):
            continue
        schema = resp.get("content", {}).get("application/json", {}).get("schema", {})
        return _schema_has_id(_resolve_ref(schema, spec), spec)
    return False


def _schema_has_id(schema: dict, spec: dict = None) -> bool:
    if not isinstance(schema, dict):
        return False
    if "$ref" in schema and spec:
        schema = _resolve_ref(schema, spec)
    for prop_name, prop_schema in schema.get("properties", {}).items():
        if "id" in prop_name.lower():
            return True
        if isinstance(prop_schema, dict):
            if _schema_has_id(prop_schema, spec):
                return True
    if "oneOf" in schema:
        for option in schema["oneOf"]:
            if isinstance(option, dict) and _schema_has_id(option, spec):
                return True
    return False


def _response_has_token(op: dict, spec: dict) -> bool:
    for code, resp in op.get("responses", {}).items():
        if not code.startswith("2"):
            continue
        schema = resp.get("content", {}).get("application/json", {}).get("schema", {})
        return _schema_has_token(_resolve_ref(schema, spec), spec)
    return False


def _schema_has_token(schema: dict, spec: dict = None) -> bool:
    if not isinstance(schema, dict):
        return False
    if "$ref" in schema and spec:
        schema = _resolve_ref(schema, spec)
    for prop_name, prop_schema in schema.get("properties", {}).items():
        if prop_name.lower().endswith("token"):
            return True
        if isinstance(prop_schema, dict):
            if _schema_has_token(prop_schema, spec):
                return True
            if "oneOf" in prop_schema:
                for option in prop_schema["oneOf"]:
                    if isinstance(option, dict):
                        if "$ref" in option and spec:
                            resolved = _resolve_ref(option["$ref"], spec)
                            if _schema_has_token(resolved, spec):
                                return True
    if "oneOf" in schema:
        for option in schema["oneOf"]:
            if isinstance(option, dict):
                if _schema_has_token(option, spec):
                    return True
                if "$ref" in option and spec:
                    resolved = _resolve_ref(option["$ref"], spec)
                    if _schema_has_token(resolved, spec):
                        return True
    return False
    for code, resp in op.get("responses", {}).items():
        if not code.startswith("2"):
            continue
        schema = resp.get("content", {}).get("application/json", {}).get("schema", {})
        return _schema_has_id(_resolve_ref(schema, spec), spec)
    return False


def _schema_has_id(schema: dict, spec: dict = None) -> bool:
    if not isinstance(schema, dict):
        return False
    if "$ref" in schema and spec:
        schema = _resolve_ref(schema, spec)
    for prop_name, prop_schema in schema.get("properties", {}).items():
        if "id" in prop_name.lower():
            return True
        if isinstance(prop_schema, dict):
            if _schema_has_id(prop_schema, spec):
                return True
    if "oneOf" in schema:
        for option in schema["oneOf"]:
            if isinstance(option, dict) and _schema_has_id(option, spec):
                return True
    return False


def _response_has_list(op: dict, spec: dict) -> bool:
    for code, resp in op.get("responses", {}).items():
        if not code.startswith("2"):
            continue
        schema = resp.get("content", {}).get("application/json", {}).get("schema", {})
        return _schema_has_list(_resolve_ref(schema, spec), spec)
    return False


def _schema_has_list(schema: dict, spec: dict = None) -> bool:
    if not isinstance(schema, dict):
        return False
    if "$ref" in schema and spec:
        schema = _resolve_ref(schema, spec)
    if schema.get("type") == "array":
        return True
    for prop_name, prop_schema in schema.get("properties", {}).items():
        if isinstance(prop_schema, dict):
            if prop_schema.get("type") == "array":
                return True
            if _schema_has_list(prop_schema, spec):
                return True
    if "oneOf" in schema:
        for option in schema["oneOf"]:
            if isinstance(option, dict) and _schema_has_list(option, spec):
                return True
    return False


def _resolve_ref(schema: dict, spec: dict) -> dict:
    if not isinstance(schema, dict):
        return {}
    if "$ref" in schema:
        parts = schema["$ref"].lstrip("#/").split("/")
        current = spec
        for part in parts:
            current = current.get(part, {})
        return _resolve_ref(current, spec) if isinstance(current, dict) else {}
    if "allOf" in schema:
        merged = {}
        for part in schema["allOf"]:
            merged.update(_resolve_ref(part, spec))
        return merged
    if "oneOf" in schema:
        # 取第一个类型
        options = schema["oneOf"]
        if options:
            first = options[0]
            if isinstance(first, dict) and "$ref" in first:
                return _resolve_ref(first, spec)
            return first if isinstance(first, dict) else {}
    return schema