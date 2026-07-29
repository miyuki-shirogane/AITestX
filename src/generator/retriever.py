import chromadb
from chromadb.utils import embedding_functions
import os
import glob


class TestCaseRetriever:
    def __init__(self, persist_dir="./knowledge_base/chroma_db"):
        self.client = chromadb.PersistentClient(path=persist_dir)
        self.embedding_fn = embedding_functions.DefaultEmbeddingFunction()
        self.collection = self.client.get_or_create_collection(
            name="test_cases",
            embedding_function=self.embedding_fn,
            metadata={"description": "历史测试用例集合"}
        )

    def load_seed_data(self, seed_dir: str):
        files = glob.glob(f"{seed_dir}/**/*.py", recursive=True)
        if not files:
            print(f"警告: {seed_dir} 下没有找到 .py 文件")
            return

        documents = []
        ids = []
        metadatas = []

        for i, filepath in enumerate(files):
            with open(filepath, "r", encoding="utf-8") as f:
                content = f.read()

            filename = os.path.basename(filepath)
            documents.append(content)
            ids.append(f"case_{i:03d}")
            metadatas.append({"filename": filename, "source": filepath})

        existing = self.collection.get()["ids"]
        if existing:
            self.collection.delete(ids=existing)

        self.collection.add(documents=documents, ids=ids, metadatas=metadatas)
        print(f"已加载 {len(documents)} 个历史用例到知识库")

    def retrieve_similar_cases(self, query: str, n_results: int = 3) -> list[str]:
        results = self.collection.query(query_texts=[query], n_results=n_results)
        return results["documents"][0] if results["documents"] else []

    @property
    def case_count(self) -> int:
        return self.collection.count()