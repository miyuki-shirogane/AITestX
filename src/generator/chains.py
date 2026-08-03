import os
import re
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate

load_dotenv()


def _clean_code_output(content: str) -> str:
    content = content.strip()
    content = re.sub(r'^```(?:python)?\s*\n', '', content)
    content = re.sub(r'\n```\s*$', '', content)
    return content


def get_llm(temperature=0.2):
    return ChatOpenAI(
        model="deepseek-chat",
        api_key=os.getenv("DEEPSEEK_API_KEY"),
        base_url=os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com"),
        temperature=temperature,
        timeout=300,
        max_retries=2,
    )


def generate_test_cases(api_doc: str, prompt_template: ChatPromptTemplate = None) -> str:
    llm = get_llm()

    if prompt_template is None:
        from .prompts.api_test import API_TEST_PROMPT
        prompt_template = API_TEST_PROMPT

    chain = prompt_template | llm
    result = chain.invoke({"api_doc": api_doc})
    return _clean_code_output(result.content)


def generate_with_rag(api_doc: str, reference_cases: list[str]) -> str:
    from .prompts.api_test import API_TEST_RAG_PROMPT

    llm = get_llm()
    reference_text = "\n\n---\n\n".join(
        case[:1500] for case in reference_cases
    )

    try:
        chain = API_TEST_RAG_PROMPT | llm
        result = chain.invoke({
            "api_doc": api_doc,
            "reference_cases": reference_text,
            "naming_style": "test_<功能>_<场景>",
        })
        return _clean_code_output(result.content)
    except Exception as e:
        print(f"RAG生成失败 ({e})，回退到普通模式...")
        return generate_test_cases(api_doc)