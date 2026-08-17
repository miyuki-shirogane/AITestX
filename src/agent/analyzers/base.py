"""Agent 基类：共享 LLM 调用、重试、知识库检索"""

import json
import os
import time
import fnmatch
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage

load_dotenv()

MAX_RETRIES = 3
RETRY_DELAY = 60


def _get_llm():
    return ChatOpenAI(
        model="deepseek-chat",
        api_key=os.getenv("DEEPSEEK_API_KEY"),
        base_url=os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com"),
        temperature=0,
        timeout=300,
        max_retries=2,
    )


def _call_llm_with_retry(llm, messages: list, step_name: str) -> str:
    for attempt in range(MAX_RETRIES):
        try:
            result = llm.invoke(messages)
            return result.content
        except Exception as e:
            msg = str(e)
            if "520" in msg or "429" in msg or "insufficient_quota" in msg:
                if attempt < MAX_RETRIES - 1:
                    delay = RETRY_DELAY * (attempt + 1)
                    print(f"      ⏳ {step_name} API {msg[:50]}... {delay}s后重试({attempt+1}/{MAX_RETRIES})")
                    time.sleep(delay)
                    continue
            raise


def _parse_json_response(raw: str) -> dict:
    content = raw.strip()
    if "```json" in content:
        content = content.split("```json")[1].split("```")[0]
    elif "```" in content:
        content = content.split("```")[1].split("```")[0]
    try:
        return json.loads(content)
    except json.JSONDecodeError:
        return {"raw": content, "parse_error": True}


class BaseAgent:
    """Agent 基类：角色 prompt + LLM 调用 + 知识库检索"""

    def __init__(self, name: str, system_prompt: str):
        self.name = name
        self.system_prompt = system_prompt
        self._llm = None

    @property
    def llm(self):
        if self._llm is None:
            self._llm = _get_llm()
        return self._llm

    def _retrieve_knowledge(self, evidence: dict) -> dict:
        """检索与当前失败相关的知识库内容"""
        api_path = evidence.get("request", {}).get("path", "")
        concepts = _load_domain_concepts()
        heuristics = _load_testing_heuristics()

        relevant_concepts = []
        for c in concepts:
            for pattern in c.get("applies_to", []):
                if _path_matches(api_path, pattern):
                    relevant_concepts.append(c)
                    break

        return {
            "concepts": relevant_concepts,
            "heuristics": heuristics,
        }

    def _build_human_message(self, evidence: dict, knowledge: dict) -> str:
        """子类重写此方法构建 human message"""
        raise NotImplementedError

    def run(self, evidence: dict) -> dict:
        knowledge = self._retrieve_knowledge(evidence)
        human_text = self._build_human_message(evidence, knowledge)
        messages = [
            SystemMessage(content=self.system_prompt),
            HumanMessage(content=human_text),
        ]
        raw = _call_llm_with_retry(self.llm, messages, self.name)
        return _parse_json_response(raw)


def _load_domain_concepts() -> list:
    path = "knowledge_base/domain_concepts.json"
    if os.path.exists(path):
        with open(path) as f:
            return json.load(f).get("concepts", [])
    return []


def _load_testing_heuristics() -> list:
    path = "knowledge_base/testing_heuristics.json"
    if os.path.exists(path):
        with open(path) as f:
            return json.load(f).get("heuristics", [])
    return []


def _path_matches(api_path: str, pattern: str) -> bool:
    return fnmatch.fnmatch(api_path, pattern)