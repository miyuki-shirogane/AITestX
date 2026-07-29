from .retriever import TestCaseRetriever
from .chains import generate_with_rag


class TestCaseGenerator:
    def __init__(self):
        self.retriever = TestCaseRetriever()

    def generate(self, api_doc: str) -> str:
        reference_cases = self.retriever.retrieve_similar_cases(api_doc, n_results=1)
        if reference_cases:
            return generate_with_rag(api_doc, reference_cases)
        else:
            from .chains import generate_test_cases
            return generate_test_cases(api_doc)