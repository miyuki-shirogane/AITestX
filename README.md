# AITestX 🧪

> AI-Native test automation platform. Feed it Swagger, get runnable pytest suites. Failing assertions? It heals itself.

## Quick Start 🚀

```bash
# 1. Configure
cp .env.example .env
# Edit .env with your LLM API key and target project info

# 2. Install
pip install -r requirements.txt

# 3. Parse Swagger
python main.py swagger swagger.json

# 4. Analyze dependencies
python main.py deps

# 5. Generate test cases
python main.py batch

# 6. Run & self-heal
python main.py heal
```

## Highlights ✨

### Smart Test Generation 🤖

- **Deep Swagger Parsing** — Recursively resolves `$ref`, `allOf`, `oneOf` to extract full request/response schemas. Enum values, array items, field constraints — nothing is flattened to `"string"`.
- **Auto Dependency Analysis** — Identifies upstream relationships from path params and request body fields. Supports 3-level recursive chains. Generates fixtures that call upstream APIs for real data instead of hardcoded placeholders.
- **Post-Generation Validation** — Auto-fixes missing imports (`os`, `allure`, `jmespath`, `pformat`, `json`), duplicate `Bearer` prefixes, and invalid matchers. No manual cleanup needed.
- **Auth Decoupled** — Configure any authentication method via `AUTH_URL` / `AUTH_BODY` / `AUTH_TOKEN_PATH` env vars. Switch projects by changing `.env` only.

### Self-Healing Engine 🔧

- **Intent Analysis** — Compares what the test expects against what the API actually returns. Same intent? Fix the assertion. Different intent? Flag for manual review.
- **Multi-Round Iteration** — Fixes 5 assertions per round, re-runs to verify, repeats until all pass or max rounds reached.
- **Resumable** — `Ctrl+C` anytime. Progress saved to checkpoint. Pick up where you left off.

### Quality of Life 🛡️

- **Manual Edit Protection** — `swagger` command never overwrites hand-edited markdown docs
- **Incremental Updates** — `swagger --diff` only updates changed endpoints
- **Filename Sanitization** — Auto-removes `-`, `{`, `}` from filenames for editor compatibility

## Commands 📋

```bash
python main.py deps       # Analyze upstream/downstream dependencies
python main.py swagger    # Parse Swagger → Markdown
python main.py generate   # Generate a single test file
python main.py batch      # Batch generate all (resumable)
python main.py heal       # Self-healing engine (resumable)
python main.py report     # Generate heal report
```

## Environment Variables ⚙️

```bash
DEEPSEEK_API_KEY          # LLM API key
DEEPSEEK_BASE_URL         # LLM API base URL
SWAGGER_PATH              # Path to Swagger JSON/YAML
BASE_URL                  # Target API base URL
AUTH_URL                  # Auth endpoint path
AUTH_BODY                 # Auth request body (JSON string)
AUTH_TOKEN_PATH           # Token path in response, e.g. data.accessToken
```

## Tech Stack 🛠️

Python · DeepSeek · ChromaDB · ONNX Embedding · PyHamcrest · pytest · Allure

## Project Structure 📁

```
src/
├── generator/       # Phase 1: Test generation
│   ├── swagger.py   # Swagger parsing engine
│   ├── deps.py      # Dependency analysis
│   ├── chains.py    # LLM calls + Prompt
│   └── prompts/     # Prompt templates
├── agent/           # Phase 2: Self-healing
│   ├── healer.py    # Resumable batch healer
│   ├── self_healing.py  # Failure analysis + auto-fix
│   └── tools/       # pytest / file tools
└── api_client.py    # HTTP client
```