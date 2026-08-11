import json
import re


def match(deps: list[dict], swagger_path: str) -> list[dict]:
    """为每个依赖匹配候选上游接口

    匹配策略：
    1. 从占位符提取关键词（如 valid_design_id → design）
    2. 在 Swagger 中搜索包含关键词的路径
    3. 排除 action 类接口（delete, cancel, submit 等）
    4. 优先选择 search/查询类接口
    5. 验证响应包含 id 字段或列表
    """
    with open(swagger_path) as f:
        spec = json.load(f)

    for dep in deps:
        keyword = dep["keyword"]
        dep["candidates"] = _search_candidates(keyword, spec)

    return deps


def _search_candidates(keyword: str, spec: dict) -> list[dict]:
    candidates = []
    action_words = ["delete", "cancel", "accept", "reject", "remove", "submit"]

    for path, methods in spec.get("paths", {}).items():
        for method in ["get", "post"]:
            if method not in methods:
                continue
            op = methods[method]
            path_lower = path.lower()
            summary = (op.get("summary") or "").lower()

            # 关键词必须在路径中
            if keyword not in path_lower:
                continue

            # 排除 action 类
            if any(w in path_lower for w in action_words):
                continue

            score = 0
            # 搜索/查询类最高优先级
            if "search" in path_lower or "查询" in summary or "分页" in summary:
                score += 5
            # 返回列表加分
            if _has_list_response(op, spec):
                score += 3
            # 返回 ID 字段加分
            if _has_id_field(op, spec):
                score += 2
            # 创建类也加分（create 返回 ID）
            if "create" in path_lower:
                score += 1

            candidates.append({
                "path": path,
                "method": method.upper(),
                "score": score,
                "has_list": _has_list_response(op, spec),
                "summary": op.get("summary", ""),
            })

    candidates.sort(key=lambda x: -x["score"])
    return candidates[:3]


def _has_list_response(op: dict, spec: dict) -> bool:
    for code, resp in op.get("responses", {}).items():
        if not code.startswith("2"):
            continue
        schema = resp.get("content", {}).get("application/json", {}).get("schema", {})
        schema = _resolve_ref(schema, spec)
        schema_str = str(schema).lower()
        if "items" in schema_str or "array" in schema_str:
            return True
    return False


def _has_id_field(op: dict, spec: dict) -> bool:
    for code, resp in op.get("responses", {}).items():
        if not code.startswith("2"):
            continue
        schema = resp.get("content", {}).get("application/json", {}).get("schema", {})
        schema = _resolve_ref(schema, spec)
        props = str(schema.get("properties", {})).lower()
        if '"id"' in props or "designid" in props or "taskid" in props:
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
        return current if isinstance(current, dict) else {}
    if "allOf" in schema:
        merged = {}
        for part in schema["allOf"]:
            merged.update(_resolve_ref(part, spec))
        return merged
    return schema