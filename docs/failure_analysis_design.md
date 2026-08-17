# 失败用例多 Agent 分析 — 设计文档 v2

> 模拟资深测试工程师排查失败用例的完整流程

---

## 1. 设计哲学

### 1.1 工具通用，知识项目特定

Agent 本身是**跨项目通用**的推理引擎，只包含角色定义和推理方法论。业务知识、测试经验、API 文档是**项目特定的配置**，运行时注入。

```
src/agent/analyzers/          ← 通用，可跨项目复用
    ├── executor.py           ← 只定义「怎么复现」
    ├── triage.py             ← 只定义「排查方法论」
    ├── contract.py           ← 只定义「契约对比方法」
    └── prompts/*.py          ← 只定义角色和推理框架

knowledge_base/               ← 项目特定，每个被测项目不同
    ├── domain_concepts.json  ← 业务概念
    ├── testing_heuristics.json ← 测试经验（跨项目通用但可覆盖）
    └── (api docs 由 swagger 解析生成)
```

### 1.2 业务知识 vs 测试专业能力

**业务知识是共享资源，不是某个角色的专属能力。**

`sourceType` 和 `designType` 的区别、接口的容错逻辑——这些是产品定义和后端设计，任何工程师都应该能查到。它应该是一个**共享知识库**，所有 Agent 都可以检索参考。

**测试专业能力才是 Agent 的角色定位。**

一个资深自动化测试工程师跨项目积累的真正能力是：

- 看到一种失败模式，能快速判断最可能的原因
- 能一眼看出生成的测试代码哪里脆弱
- 知道从哪个环节入手排查最高效
- 能判断什么失败是阻断性的、什么可以降级

### 1.2 为什么 LLM 驱动

每个 Agent 是一个 LLM + 专属角色 prompt + 共享知识库。Agent 用 LLM 做推理，知识库提供上下文。不搞规则引擎。

---

## 2. 六 Agent 架构

```
                    ┌───────────────────────────────────────┐
                    │           Coordinator                 │
                    │   汇总 + 冲突裁决 + 风险评估 + 报告     │
                    └───────────────┬───────────────────────┘
                                    │
          ┌──────────┬──────────────┼──────────────┬──────────┐
          ▼          ▼              ▼              ▼          ▼
   ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐
   │ Executor │ │  Triage  │ │ Contract │ │  Data    │ │ Environ. │
   │ 复现+取证 │ │ Specialist│ │ Analyst  │ │  Path    │ │  Checker │
   │          │ │ 排查策略  │ │ 契约对比  │ │  Tracer  │ │ 环境诊断  │
   └────┬─────┘ └────┬─────┘ └────┬─────┘ └────┬─────┘ └────┬─────┘
        │            │            │            │            │
        ▼            ▼            ▼            ▼            ▼
   请求/响应体   失败模式匹配  断言 vs 契约  fixture 链   网络/环境
   traceback    排查建议      字段类型      数据有效性   是否偶发
        │            │            │            │            │
        └────────────┴────────────┴────────────┴────────────┘
                                    │
                            ┌───────┴───────┐
                            │  共享知识库    │
                            │  业务概念     │
                            │  API 文档     │
                            └───────────────┘
```

### 各 Agent 一句话

| Agent | 回答的问题 | 注入的测试专业能力 |
|-------|-----------|------------------|
| **Executor** | 「实际发生了什么？」 | —（纯工具） |
| **Triage Specialist** | 「根据错误模式，最可能的原因是什么？从哪里开始排查？」 | 失败模式识别 + 排查策略 |
| **Contract Analyst** | 「断言和 API 契约/实际响应是否一致？」 | 生成代码常见缺陷识别 |
| **Data Path Tracer** | 「fixture 链数据是否有效？」 | 数据依赖排查经验 |
| **Environment Checker** | 「是代码问题还是环境问题？」 | 环境问题识别 |
| **Coordinator** | 「综合来看，这个失败该怎么做？」 | 风险评估 + 优先级排序 |

---

## 3. 各 Agent 详细设计

### 3.1 Executor — 复现 + 取证

纯执行角色，不判断对错。只回答「实际发生了什么」。

**输入：** 失败用例名称 + 测试文件路径

**工作方式：**
- 运行 `pytest <file>::<test> --tb=long -s` 重跑单个用例
- 从 stdout 解析 `ApiClient` 日志，提取实际请求体和响应体
- 从 traceback 提取断言期望值和实际值

**产出：**

```json
{
  "test_name": "test_search_designs_by_type[房间设计]",
  "request": { "method": "POST", "path": "/...designs/search", "body": {"designType": 2} },
  "response": { "http_status": 200, "body": { "code": 200, "data": { "items": [{"sourceType": 1}] } } },
  "assertion": { "line": "assert_that(item[\"sourceType\"], equal_to(2))", "expected": "2", "actual": "1" },
  "fixture_chain": ["auth_headers"],
  "fixture_values": { "auth_headers": {"Authorization": "Bearer eyJ..."} }
}
```

---

### 3.2 Triage Specialist — 排查策略

**定位：** 这是你测试经验的第一个核心注入点。看到错误模式，快速判断最可能的原因和排查路径。

**输入：** Executor 产出 + 共享知识库（业务概念 + API 文档）

**Prompt 结构：**

```
【角色】
你是资深测试排查专家。你经手过大量自动化测试失败案例，能根据错误模式快速判断最可能的原因。

你的专业经验包括：
- 当看到 "KeyError: 'code'" 且响应体是 {"_status": N, "_body": ""} → 这是 ApiClient 对非 JSON 响应的包装，断言用了 resp["code"] 但实际应该用 resp.get("_status", resp.get("code"))
- 当看到 parametrized 用例中部分通过、部分失败 → 失败的参数组合通常是 API 实际不支持但文档标注支持的边界值
- 当看到同一个字段名在多次 heal 中来回修改 → 断言陷入了振荡，需要自适应断言
- 当看到 409 Conflict → 大概率是 fixture 取到的数据已被占用，需要遍历数据列表而非固定取 items[0]
- 当看到 fixture 链中的测试失败，但被测试接口本身没问题 → 上游依赖问题，需要追溯 fixture 的数据来源

【共享知识库 — 当前接口相关】
{{ 从知识库检索的业务概念和 API 文档 }}

【当前失败】
- 测试: {{ test_name }}
- 错误: {{ error }}
- 请求: {{ request }}
- 响应: {{ response }}

【请判断】
1. 根据错误模式，最可能的原因是什么？（1-2句话）
2. 排查优先级：先查什么、再查什么？（给出具体排查步骤）
3. 这个失败属于以下哪种类型？
   - assertion_mismatch: 断言值与实际响应不匹配
   - fixture_data_issue: 测试数据或 fixture 问题
   - generated_code_flaw: AI 生成的测试代码有结构性缺陷
   - api_behavior_change: API 行为与文档/预期不一致
   - environment_issue: 环境或网络问题
4. 置信度：high / medium / low
```

**输出：**

```json
{
  "most_likely_cause": "断言期望 sourceType 等于 designType(2)，但实际 API 返回的 sourceType 始终为 1。这是 AI 生成代码的常见缺陷：假设请求参数和响应字段有对称关系，但实际它们表示不同概念。",
  "category": "generated_code_flaw",
  "confidence": "high",
  "triage_steps": [
    "1. 查看 Swagger 文档中 sourceType 字段的定义，确认其语义",
    "2. 查询知识库中是否有关于 sourceType 和 designType 关系的说明",
    "3. 如果确认语义不同，移除该断言或改为验证 sourceType 存在即可"
  ],
  "is_flaky": false
}
```

**需要你输入：** 把你排查失败的经验提炼成「错误模式 → 可能原因」的映射。这些是跨项目通用的测试经验，不是业务知识。比如：

```
- 模式: KeyError on response field + response has _status/_body → cause: ApiClient non-JSON wrapping
- 模式: parametrized test, some pass some fail → cause: boundary values not supported by API
- 模式: same field modified back and forth across heal rounds → cause: oscillation, need adaptive assertion
- 模式: 409/404 on fixture-dependent test → cause: fixture data conflict/non-existence
- 模式: test passes alone, fails in suite → cause: test ordering dependency or shared state
```

---

### 3.3 Contract Analyst — 契约对比

**定位：** 你的第二个经验注入点。AI 生成测试代码有系统性缺陷——你知道这些缺陷的模式，能快速识别。

**输入：** Executor 产出 + Swagger 文档 + 共享知识库

**Prompt 结构：**

```
【角色】
你是 API 契约分析师。你对比测试断言、API 实际响应、Swagger 文档三者。

你特别警惕 AI 生成测试代码的常见缺陷：
- 「对称性假设」：AI 假设请求参数和响应字段有对称关系（传 designType=2 就期望 sourceType=2），但实际 API 往往不对称
- 「枚举全量假设」：AI 把 Swagger 中所有枚举值都当成合法值，但实际 API 可能只接受部分枚举值
- 「字段名猜测」：AI 在没有明确文档时猜测字段名（如 code vs statusCode），导致 KeyError
- 「错误响应格式假设」：AI 假设所有错误响应都有 JSON body，但 401/403 等可能没有
- 「分页硬编码假设」：AI 假设分页参数一定有默认值，断言 pageIndex/pageSize 一定等于请求值

【Swagger 文档】
{{ 当前 API 的完整文档 }}

【当前失败】
{{ Executor 产出 }}

【请判断】
1. 这个失败是否属于上述 AI 生成代码缺陷之一？如果是，是哪种？
2. 断言、API 实际响应、Swagger 文档三者中，哪两个不一致？
3. 应该怎么修？
```

**输出：**

```json
{
  "verdict": "assertion_fix",
  "generated_code_flaw": "对称性假设",
  "reasoning": "测试断言 sourceType 应等于请求参数 designType，但 Swagger 文档中 sourceType 和 designType 是独立字段，没有文档说明它们有对应关系。这是 AI 的对称性假设缺陷。",
  "fix_suggestion": "移除 sourceType == designType 的断言，或改为验证 sourceType 存在且为合法值",
  "comparison": {
    "assertion": "sourceType == 2",
    "api_response": "sourceType = 1",
    "swagger": "sourceType: int, designType: enum"
  }
}
```

**需要你输入：** 把你发现的 AI 生成代码的系统性缺陷列出来。这些是你在使用 AI 生成测试过程中积累的观察：

```
- 对称性假设：AI 认为请求参数和响应字段一一对应
- 枚举全量假设：AI 把 Swagger enum 的所有值都当成合法输入
- 字段名猜测：AI 在文档不明确时猜字段名
- 错误响应格式假设：AI 假设所有响应都有标准 JSON body
- 分页硬编码假设：AI 假设 pageIndex/pageSize 能原样返回
- ... （你补充）
```

---

### 3.4 Data Path Tracer — 数据链追溯

**定位：** 排查 fixture 链。很多失败是被测接口没问题，但上游 fixture 没拿到有效数据。

**输入：** Executor 产出 + 依赖分析结果（`deps.py`）

**工作方式：** 追溯 fixture 链，确认每个 fixture 是否成功获取了数据。

**输出：**

```json
{
  "verdict": "fixture_ok",
  "fixture_chain_status": [
    {"fixture": "auth_headers", "status": "ok", "data": "token obtained"},
    {"fixture": "design_id", "status": "ok", "data": "designId=019fff83-..."}
  ],
  "data_validity": "valid",
  "suggestion": null
}
```

---

### 3.5 Environment Checker — 环境诊断

轻量级 Agent，区分「代码问题」和「环境抖动」。

**判断逻辑：**
- ConnectionRefused / ConnectionReset / MaxRetries / timeout → 环境问题
- 503 / 429 → 服务暂时不可用
- 同一个用例之前通过过 → 标记为 flaky（偶发）
- 其他 → 不是环境问题，交给其他 Agent

---

### 3.6 Coordinator — 协调器

**定位：** 你的第三个经验注入点。不仅能汇总，还能做风险评估和优先级排序。

**输入：** 所有 Agent 输出 + 共享知识库

**Prompt 结构：**

```
【角色】
你是测试结果分析协调器。你综合各专家的意见，做出最终判断。

你的风险评估经验：
- 401/403 认证失败 → 阻断性，所有需要认证的用例都会失败，优先修复
- 单个参数化用例失败 → 低风险，通常不影响其他用例
- 数据依赖链断裂 → 中风险，影响所有依赖该 fixture 的用例
- 搜索/查询类接口失败 → 低风险（只读操作）
- 创建/删除类接口失败 → 高风险（影响数据状态）

【各专家意见】
{{ 所有 Agent 的输出 }}

【请输出】
1. 最终结论：auto_fix / ignore / needs_manual / file_bug
2. 风险等级：blocker / high / medium / low
3. 修复建议（如果 auto_fix）
4. 为什么采纳/拒绝了某些 Agent 的意见
```

**冲突裁决：** 当 Agent 意见冲突时，Coordinator 需要解释为什么采纳 A 而不是 B。比如 Triage Specialist 说 `generated_code_flaw`，Contract Analyst 说 `assertion_fix`——两者其实不冲突，Coordinator 应该合并为「断言需要修复，根因是 AI 生成代码的对称性假设缺陷」。

---

## 4. 共享知识库

业务规则不属于任何 Agent，是共享资源。所有 Agent 在需要时检索。

### 4.1 组织方式：按概念而非按接口

```json
{
  "concepts": [
    {
      "id": "concept_sourceType",
      "name": "sourceType 字段",
      "knowledge": "sourceType 表示设计的生成来源。目前所有设计都是 AI 生成，所以值始终为 1。与请求参数 designType（筛选条件）是两个不同概念。",
      "applies_to": ["*_designs_search", "*_designs_*"],
      "impact": "测试不应断言 sourceType 等于 designType 或任何其他请求参数"
    },
    {
      "id": "concept_designType_validation",
      "name": "designType 参数校验",
      "knowledge": "designType 是 FluentValidation 校验的枚举参数。合法值：1=House, 2=Room。值 0=Unknown 虽然在 Swagger 枚举定义中，但实际校验会拒绝。字符串类型的非法值会被 JSON 反序列化阶段拦截，返回的响应格式可能与标准 400 不同。",
      "applies_to": ["*designs_search", "*design_proposals", "*house_construction"],
      "impact": "designType=0 应断言 400 而非 200。designType=字符串类型可能返回非标准格式错误。"
    }
  ]
}
```

### 4.2 业务概念库

业务概念已在 4.1 中按概念组织。所有 Agent 均可在需要时检索。

---

## 5. 你需要输入的核心内容

### 5.1 排查经验（给 Triage Specialist）

把你跨项目积累的「看到这种错误 → 大概率是那个原因」的经验写出来：

```
错误模式                          →  最可能原因
──────────────────────────────────────────────────
KeyError + _status/_body          →  ApiClient 非 JSON 响应包装
parametrized 部分通过部分失败       →  边界值 API 不支持
同一字段在 heal 中来回修改          →  断言振荡，需要自适应断言
409/404 + fixture 依赖             →  fixture 数据冲突/不存在
单跑通过、合跑失败                  →  测试间状态污染
```

### 5.2 AI 生成代码缺陷（给 Contract Analyst）

把你观察到的 AI 生成测试的系统性缺陷列出来：

```
缺陷类型              表现                              示例
──────────────────────────────────────────────────────────────────
对称性假设            断言请求参数 == 响应字段             designType=2 → 期望 sourceType=2
枚举全量假设          把 Swagger enum 所有值当合法输入     designType=0 期望 200
字段名猜测            文档不明确时猜字段名                  code vs statusCode
错误响应格式假设      假设所有响应都有 JSON body           401 断言 resp["code"]
```

### 5.3 风险评估经验（给 Coordinator）

```
失败类型              风险等级    原因
─────────────────────────────────────────
401/403 认证失败       blocker    阻断所有认证用例
fixture 链断裂          high      影响所有依赖该 fixture 的用例
单个参数化用例失败       low       不影响其他用例
搜索/查询类接口失败      low       只读操作
```

### 5.4 业务概念（共享知识库）

按概念组织，标注影响范围，不绑定特定接口。

---

## 6. 和现有模块的关系

```
python main.py
     │
     ├── batch      Phase 1: AI 生成测试用例
     ├── heal       Phase 2: 自动修断言（修改代码）
     ├── analyze    Phase 2.5: 多 Agent 深度分析（只读，输出报告）
     └── report     生成 pytest 日志 + 分析汇总
```

推荐流程：`batch` → `heal` → `analyze`（对 heal 后剩余失败做深度分析）

---

## 7. 执行模型

```
for each 失败用例:
    ┌──────────────────────────────────────────────┐
    │  1. Executor 复现（串行，必须先跑）              │
    │     产出: 请求/响应/断言/traceback             │
    └──────────────────┬───────────────────────────┘
                       │
         ┌─────────────┼─────────────┐
         ▼             ▼             ▼
   ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐
   │  Triage  │ │ Contract │ │  Data    │ │ Environ. │
   │Specialist│ │ Analyst  │ │  Path    │ │ Checker  │
   │          │ │          │ │  Tracer  │ │          │
   └────┬─────┘ └────┬─────┘ └────┬─────┘ └────┬─────┘
        │            │            │            │
        └────────────┼────────────┴────────────┘
                     │        （并行，4 个 Agent 同时分析）
                     ▼
   ┌──────────────────────────────────────────────┐
   │  2. Coordinator 汇总裁决                       │
   └──────────────────────────────────────────────┘
                     │
                     ▼
              追加到报告
```

**设计理由：**
- 用例串行进入：避免多个用例的 Executor 并行运行互相干扰（共享 fixture、session 状态等）
- 单个用例内 Agent 并行：Executor 产出证据后，四个分析 Agent 可以同时工作，互不依赖
- Coordinator 最后汇总：需要等四个 Agent 都完成才能做冲突裁决

---

## 8. 技术选型与框架评估

### 8.1 技术选型

| 选项 | 优点 | 缺点 | 适合度 |
|------|------|------|--------|
| **直接复用现有 LangChain 模式** | 项目已有 `ChatOpenAI` + `ChatPromptTemplate` 封装，`self_healing.py` 已实现带重试的 LLM 调用 | 并行执行需要自己用 `concurrent.futures` 实现 | ⭐⭐⭐ 推荐 |
| **LangGraph** | 内置 state machine、条件分支、并行节点 | 重依赖，学习成本高，当前项目规模用不上 | ⭐⭐ |
| **CrewAI / AutoGen** | 专为多 Agent 设计 | 又一套框架，侵入性大 | ⭐ |

**推荐：直接复用现有模式。** 理由：

1. `src/agent/self_healing.py` 已经有 `_get_llm()` + `_call_llm_with_retry()` 的成熟封装
2. 并行执行用 `concurrent.futures.ThreadPoolExecutor` 即可，四个 Agent 的 LLM 调用都是 I/O 密集型
3. 没有引入新依赖

### 8.2 目录结构

```
src/agent/analyzers/
├── __init__.py              # 导出主入口 analyze()
├── base.py                  # BaseAgent: 共享的 LLM 调用 + 重试 + 知识库检索
├── executor.py              # Executor: 运行 pytest 子进程，解析日志
├── triage.py                # Triage Specialist
├── contract.py              # Contract Analyst
├── data_path.py             # Data Path Tracer
├── environment.py           # Environment Checker
├── coordinator.py           # Coordinator: 汇总 + 生成报告
└── prompts/
    ├── __init__.py
    ├── triage.py
    ├── contract.py
    ├── data_path.py
    ├── environment.py
    └── coordinator.py
```

### 8.3 对现有代码的侵入性

| 改动点 | 类型 | 影响 |
|--------|------|------|
| `src/agent/analyzers/` | **新增** | 无影响，独立模块 |
| `main.py` 新增 `cmd_analyze` | **新增** | 加一个 CLI 命令，不改现有代码 |
| `knowledge_base/domain_concepts.json` | **新增** | 无影响，纯配置文件 |
| `knowledge_base/testing_heuristics.json` | **新增** | 无影响，纯配置文件 |
| `src/agent/self_healing.py` | **不改** | 复用其 `_get_llm()` 和 `_call_llm_with_retry()` |
| `src/generator/deps.py` | **不改** | 复用依赖分析结果 |
| `src/generator/swagger.py` | **不改** | 复用已解析的 API 文档 |
| heal / generate / batch | **不改** | 完全独立 |

**总结：零侵入。** 新模块在 `src/agent/analyzers/` 下独立运行，只复用现有工具函数，不修改任何现有代码。

### 8.4 依赖关系

```
src/agent/analyzers/
    │
    ├── 依赖（复用，不修改）─────────────────────
    │   ├── src/agent/self_healing.py  → _get_llm(), _call_llm_with_retry()
    │   ├── src/api_client.py          → ApiClient（Executor 可能需要）
    │   └── src/generator/deps.py      → 依赖分析结果（Data Path Tracer）
    │
    ├── 新增配置───────────────────────────────
    │   ├── knowledge_base/domain_concepts.json
    │   └── knowledge_base/testing_heuristics.json
    │
    └── 输出───────────────────────────────────
        └── reports/analyze_report.md
```