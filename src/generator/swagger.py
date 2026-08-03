import json
import re
import requests
import yaml


def parse_swagger(source: str) -> list[dict]:
    """解析 Swagger/OpenAPI 文档，返回每个接口的 Markdown 描述

    source 可以是 URL 或本地文件路径
    返回: [{"path": "POST /api/login", "doc": "markdown...", "tag": "用户"}, ...]
    """
    spec = _load_spec(source)
    base_path = spec.get("servers", [{}])[0].get("url", "").rstrip("/")
    if not base_path and "host" in spec:
        scheme = spec.get("schemes", ["http"])[0]
        base_path = f"{scheme}://{spec['host']}{spec.get('basePath', '')}"

    results = []
    for path, methods in spec.get("paths", {}).items():
        for method in ["get", "post", "put", "delete", "patch"]:
            if method not in methods:
                continue
            op = methods[method]
            doc = _build_markdown(op, method.upper(), path, base_path)
            tag = (op.get("tags") or ["未分类"])[0]
            results.append({"path": f"{method.upper()} {path}", "doc": doc, "tag": tag})

    return results


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


def _build_markdown(op: dict, method: str, path: str, base_path: str) -> str:
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
            ptype = _get_param_type(p)
            required = "是" if p.get("required") else "否"
            desc = p.get("description", "")
            lines.append(f"| {name} | {location} | {ptype} | {required} | {desc} |")
        lines.append("")

    if request_body:
        lines.append("## 请求体")
        lines.append("")
        content = request_body.get("content", {})
        json_schema = content.get("application/json", {}).get("schema", {})
        if json_schema:
            lines.append("```json")
            lines.append(json.dumps(_schema_to_example(json_schema), indent=2, ensure_ascii=False))
            lines.append("```")
            lines.append("")
            lines.append("字段说明：")
            lines.append("")
            for prop, prop_schema in json_schema.get("properties", {}).items():
                required_list = json_schema.get("required", [])
                req = "必填" if prop in required_list else "可选"
                ptype = _get_schema_type(prop_schema)
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
            if json_schema:
                lines.append("```json")
                lines.append(json.dumps(_schema_to_example(json_schema), indent=2, ensure_ascii=False))
                lines.append("```")
            lines.append("")

    return "\n".join(lines)


def _get_param_type(param: dict) -> str:
    schema = param.get("schema", {})
    if schema:
        return _get_schema_type(schema)
    return param.get("type", "string")


def _get_schema_type(schema: dict) -> str:
    if not schema:
        return "string"
    stype = schema.get("type", "object")
    if stype == "array":
        items = schema.get("items", {})
        return f"array[{_get_schema_type(items)}]"
    if stype == "integer":
        return "int"
    if stype == "number":
        return "float"
    return stype


def _schema_to_example(schema: dict) -> dict:
    if not schema:
        return {}
    example = {}
    for prop, prop_schema in schema.get("properties", {}).items():
        stype = _get_schema_type(prop_schema)
        example_val = prop_schema.get("example")
        if example_val is not None:
            example[prop] = example_val
        elif stype == "int":
            example[prop] = 0
        elif stype == "float":
            example[prop] = 0.0
        elif stype == "array[string]":
            example[prop] = ["string"]
        elif stype == "array[int]":
            example[prop] = [0]
        elif stype == "boolean":
            example[prop] = True
        else:
            example[prop] = "string"
    return example