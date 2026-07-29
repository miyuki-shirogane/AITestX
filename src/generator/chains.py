import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate

load_dotenv()


def get_llm(temperature=0.2):
    return ChatOpenAI(
        model="deepseek-chat",
        api_key=os.getenv("DEEPSEEK_API_KEY"),
        base_url=os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com"),
        temperature=temperature,
    )


def generate_test_cases(api_doc: str, prompt_template: ChatPromptTemplate = None) -> str:
    llm = get_llm()

    if prompt_template is None:
        from .prompts.api_test import API_TEST_PROMPT
        prompt_template = API_TEST_PROMPT

    chain = prompt_template | llm
    result = chain.invoke({"api_doc": api_doc})
    return result.content


def generate_with_rag(api_doc: str, reference_cases: list[str]) -> str:
    from .prompts.api_test import API_TEST_RAG_PROMPT

    llm = get_llm()
    reference_text = "\n\n---\n\n".join(reference_cases)

    chain = API_TEST_RAG_PROMPT | llm
    result = chain.invoke({
        "api_doc": api_doc,
        "reference_cases": reference_text,
        "naming_style": "test_<功能>_<场景>",
        "assertion_style": "pytest标准assert",
    })
    return result.content