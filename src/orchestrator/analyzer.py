import re
import subprocess
import glob
import os


def analyze(output_dir: str = "output") -> list[dict]:
    """分析失败用例，返回依赖列表

    返回: [{"keyword": "design", "placeholder": "valid_design_id", "files": ["test_xxx.py"], "test_count": 3}, ...]
    """
    deps = []

    for f in sorted(glob.glob(f"{output_dir}/*.py")):
        with open(f) as fh:
            content = fh.read()

        if "@pytest.mark.skip" in content:
            continue

        placeholders = _extract_placeholders(content)
        if not placeholders:
            continue

        result = subprocess.run(
            ["pytest", f, "--tb=no", "-q", "--no-header"],
            capture_output=True, text=True, timeout=30
        )
        if "FAILED" not in (result.stdout + result.stderr):
            continue

        for placeholder, keyword in placeholders:
            if not keyword or len(keyword) < 2:
                continue
            existing = next((d for d in deps if d["placeholder"] == placeholder), None)
            if existing:
                existing["files"].append(os.path.basename(f))
            else:
                deps.append({
                    "keyword": keyword,
                    "placeholder": placeholder,
                    "files": [os.path.basename(f)],
                })

    return deps


def _extract_placeholders(content: str) -> list[tuple]:
    """从测试代码中提取占位符，返回 [(placeholder, keyword), ...]"""
    results = []
    for m in re.finditer(r'"valid_(\w+)"', content):
        raw = m.group(1)
        # 去掉尾部数字: design_id_123 → design_id
        clean = re.sub(r'_\d+$', '', raw)
        keyword = clean.replace("_id", "").strip("_")
        results.append((f"valid_{clean}", keyword))
    return results