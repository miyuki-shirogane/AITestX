from .analyzer import analyze
from .matcher import match
from .generator import generate


def orchestrate(output_dir: str = "output", swagger_path: str = "target_service/solgrid-friend-full.json"):
    """Phase 3 主入口：分析依赖 → 匹配上游 → 生成 fixture

    config 从环境变量读取，不硬编码项目信息
    """
    import os
    from dotenv import load_dotenv
    load_dotenv()

    config = {
        "base_url": os.getenv("BASE_URL", "https://solgrid-friend-api.rivtower.cc"),
        "login_path": os.getenv("LOGIN_PATH", "/api/v1/user/login"),
        "token_path": os.getenv("TOKEN_PATH", "data.accessToken"),
    }

    print("=" * 60)
    print("AITestX Phase 3 - 上游依赖编排")
    print("=" * 60)

    print(f"\n📋 配置: {config['base_url']}")

    print("\n1. 分析失败的测试用例...")
    deps = analyze(output_dir)
    if not deps:
        print("   没有发现需要上游数据的用例")
        return
    for dep in deps:
        print(f"   {dep['placeholder']}: 关键词={dep['keyword']}, {len(dep['files'])} 个文件")

    print("\n2. 匹配候选上游接口...")
    deps = match(deps, swagger_path)
    for dep in deps:
        candidates = dep.get("candidates", [])
        if candidates:
            best = candidates[0]
            print(f"   {dep['placeholder']} → {best['method']} {best['path']} (score={best['score']})")
            for c in candidates[1:3]:
                print(f"       备选: {c['method']} {c['path']} (score={c['score']})")
        else:
            print(f"   {dep['placeholder']} → 未找到匹配")

    print("\n3. 生成 conftest.py...")
    generate(deps, config, output_dir)
    print(f"   已保存到 {output_dir}/conftest.py")
    print(f"\n💡 修改测试文件：将 xxx = 'valid_yyy' 替换为 fixture 参数 {deps[0]['placeholder']} 即可")