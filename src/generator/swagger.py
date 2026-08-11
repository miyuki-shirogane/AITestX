import json
import re
import hashlib
import os
import requests
import yaml


HASH_FILE = "target_service/.api_hashes.json"


def load_hashes() -> dict:
    if os.path.exists(HASH_FILE):
        with open(HASH_FILE) as f:
            return json.load(f)
    return {}


def save_hashes(hashes: dict):
    os.makedirs(os.path.dirname(HASH_FILE), exist_ok=True)
    with open(HASH_FILE, "w") as f:
        json.dump(hashes, f, ensure_ascii=False, indent=2)


def hash_content(content: str) -> str:
    return hashlib.md5(content.encode()).hexdigest()


def parse_swagger(source: str, diff_only: bool = False) -> tuple:
    """解析 Swagger/OpenAPI 文档，返回 (接口列表, 变更统计)"""
    spec = _load_spec(source)
    base_path = spec.get("servers", [{}])[0].get("url", "").rstrip("/")
    if not base_path and "host" in spec:
        scheme = spec.get("schemes", ["http"])[0]
        base_path = f"{scheme}://{spec['host']}{spec.get('basePath', '')}"

    old_hashes = load_hashes()
    new_hashes = {}
    results = []
    changed = 0
    unchanged = 0
    new_count = 0

    for path, methods in spec.get("paths", {}).items():
        for method in ["get", "post", "put", "delete", "patch"]:
            if method not in methods:
                continue
            op = methods[method]
            doc = _build_markdown(op, method.upper(), path, base_path, spec)
            tag = (op.get("tags") or ["未分类"])[0]
            api_path = f"{method.upper()} {path}"
            safe_name = api_path.replace("/", "_").replace(" ", "_").replace("-", "_").replace("{", "_").replace("}", "_").strip("_")
            key = f"{safe_name}.md"
            h = hash_content(doc)
            new_hashes[key] = h

            if diff_only:
                old_h = old_hashes.get(key)
                if old_h == h:
                    unchanged += 1
                    continue
                elif old_h is None:
                    new_count += 1
                else:
                    changed += 1

            results.append({"path": api_path, "doc": doc, "tag": tag, "filename": key})

    save_hashes(new_hashes)
    return results, {"total": len(results), "changed": changed, "new": new_count, "unchanged": unchanged}


def _load_spec(source: str) -> dict:
    if source.startswith("http://") or source.startswith("https://"):
        resp = requests.get(source, timeout=30)
        resp.raise_for_status()
        content = resp.text
    else:
        with open(source, "r", encoding="utf-8") as f:
            content = f.read()

    if content.strip().startswith("{"):
        return json.loads(content)
    return yaml.safe_load(content)


def _resolve_ref(ref: str, spec: dict) -> dict:
    if not ref or not ref.startswith("#/"):
        return {}
    parts = ref.lstrip("#/").split("/")
    current = spec
    for part in parts:
        current = current.get(part, {})
    return current if isinstance(current, dict) else {}


def _build_markdown(op: dict, method: str, path: str, base_path: str, spec: dict) -> str:
    summary = op.get("summary", "")
    description = op.get("description", "")
    tag = (op.get("tags") or ["未分类"])[0]
    params = op.get("parameters", [])
    request_body = op.get("requestBody", {})
    responses = op.get("responses", {})

    title = summary or f"{method} {path}"

    lines = [f"# {title}", "", f"{method} {base_path}{path}", "", f"所属模块: {tag}", ""]

    if description:
        lines.append(description)
        lines.append("")

    if params:
        lines.append("## 请求参数")
        lines.append("")
        lines.append("| 参数名 | 位置 | 类型 | 必填 | 说明 |")
        lines.append("|--------|------|------|------|------|")
        for p in params:
            name = p.get("name", "")
            location = p.get("in", "")
            ptype = _get_param_type(p, spec)
            required = "是" if p.get("required") else "否"
            desc = p.get("description", "")
            lines.append(f"| {name} | {location} | {ptype} | {required} | {desc} |")
        lines.append("")

    if request_body:
        lines.append("## 请求体")
        lines.append("")
        content = request_body.get("content", {})
        json_schema = content.get("application/json", {}).get("schema", {})
        json_schema = _resolve_ref(json_schema.get("$ref", ""), spec) or json_schema
        if json_schema:
            lines.append("```json")
            lines.append(json.dumps(_schema_to_example(json_schema, spec), indent=2, ensure_ascii=False))
            lines.append("```")
            lines.append("")
            lines.append("字段说明：")
            lines.append("")
            for prop, prop_schema in json_schema.get("properties", {}).items():
                required_list = json_schema.get("required", [])
                req = "必填" if prop in required_list else "可选"
                ptype = _get_schema_type(prop_schema, spec)
                desc = prop_schema.get("description", "")
                lines.append(f"- `{prop}`: {ptype}, {req}{f', {desc}' if desc else ''}")
            lines.append("")

    if responses:
        lines.append("## 响应")
        lines.append("")
        for code, resp in responses.items():
            resp_desc = resp.get("description", "")
            lines.append(f"**{code}**: {resp_desc}")
            content = resp.get("content", {})
            json_schema = content.get("application/json", {}).get("schema", {})
            json_schema = _resolve_ref(json_schema.get("$ref", ""), spec) or json_schema
            if json_schema:
                lines.append("```json")
                lines.append(json.dumps(_schema_to_example(json_schema, spec), indent=2, ensure_ascii=False))
                lines.append("```")
            lines.append("")

    return "\n".join(lines)


def _get_param_type(param: dict, spec: dict = None) -> str:
    schema = param.get("schema", {})
    if schema:
        return _get_schema_type(schema, spec)
    return param.get("type", "string")


def _get_schema_type(schema: dict, spec: dict = None) -> str:
    if not schema:
        return "string"
    if "$ref" in schema and spec:
        schema = _resolve_ref(schema["$ref"], spec) or schema
    stype = schema.get("type", "object")
    if stype == "array":
        items = schema.get("items", {})
        return f"array[{_get_schema_type(items, spec)}]"
    if stype == "integer":
        return "int"
    if stype == "number":
        return "float"
    if stype == "boolean":
        return "boolean"
    return stype


def _schema_to_example(schema: dict, spec: dict = None) -> dict:
    if not schema:
        return {}
    if "$ref" in schema and spec:
        schema = _resolve_ref(schema["$ref"], spec) or schema
    if "allOf" in schema:
        merged = {}
        for part in schema["allOf"]:
            resolved = _resolve_ref(part.get("$ref", ""), spec) if part.get("$ref") else part
            merged.update(resolved.get("properties", {}))
        schema = {"type": "object", "properties": merged}
    if "oneOf" in schema:
        schema = {"type": "string", "description": "多种类型，见文档"}
    example = {}
    for prop, prop_schema in schema.get("properties", {}).items():
        resolved = _resolve_ref(prop_schema.get("$ref", ""), spec) if prop_schema.get("$ref") else prop_schema
        stype = _get_schema_type(resolved, spec)
        example_val = resolved.get("example")
        if example_val is not None:
            example[prop] = example_val
        elif stype == "int":
            example[prop] = 0
        elif stype == "float":
            example[prop] = 0.0
        elif stype.startswith("array"):
            example[prop] = []
        elif stype == "boolean":
            example[prop] = True
        else:
            example[prop] = "string"
    return example