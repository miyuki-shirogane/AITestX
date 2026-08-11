import json


def match(deps: list[dict], swagger_path: str) -> list[dict]:
    """为每个依赖匹配候选上游接口

    返回: 依赖列表，每个新增 "candidates" 字段（排名列表）
    """
    with open(swagger_path) as f:
        spec = json.load(f)

    for dep in deps:
        keyword = dep["keyword"]
        dep["candidates"] = _search_candidates(keyword, spec)

    return deps


def _search_candidates(keyword: str, spec: dict) -> list[dict]:
    """在 Swagger 中搜索匹配关键词的接口"""
    candidates = []
    action_words = ["create", "delete", "cancel", "accept", "reject", "send", "modify", "remove", "submit"]

    for path, methods in spec.get("paths", {}).items():
        for method in ["get", "post"]:
            if method not in methods:
                continue
            op = methods[method]
            summary = (op.get("summary") or "").lower()
            path_lower = path.lower()
            tags = " ".join(op.get("tags", [])).lower()

            score = 0
            if keyword in path_lower:
                score += 5
            if keyword in summary:
                score += 3
            if keyword in tags:
                score += 2
            if "search" in path_lower or "查询" in summary:
                score += 2
            if any(w in path_lower for w in action_words):
                score -= 2

            if score > 0:
                has_list = _has_list_response(op, spec)
                candidates.append({
                    "path": path,
                    "method": method.upper(),
                    "score": score,
                    "has_list": has_list,
                    "summary": op.get("summary", ""),
                })

    candidates.sort(key=lambda x: -x["score"])
    return candidates[:5]


def _has_list_response(op: dict, spec: dict) -> bool:
    """检查响应是否包含列表"""
    for code, resp in op.get("responses", {}).items():
        if not code.startswith("2"):
            continue
        schema = resp.get("content", {}).get("application/json", {}).get("schema", {})
        if "$ref" in schema:
            schema = _resolve_ref(schema["$ref"], spec)
        schema_str = str(schema).lower()
        if "items" in schema_str or "array" in schema_str:
            return True
    return False


def _resolve_ref(ref: str, spec: dict) -> dict:
    parts = ref.lstrip("#/").split("/")
    current = spec
    for part in parts:
        current = current.get(part, {})
    return current if isinstance(current, dict) else {}