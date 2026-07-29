import json
import os
import glob
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


class TestCaseRetriever:
    def __init__(self, persist_dir="./knowledge_base/tfidf_index"):
        self.persist_dir = persist_dir
        self.documents = []
        self.ids = []
        self.metadatas = []
        self.vectorizer = None
        self.matrix = None
        self._load()

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

        self.vectorizer = TfidfVectorizer(max_features=5000)
        self.matrix = self.vectorizer.fit_transform(documents)
        self.documents = documents
        self.ids = ids
        self.metadatas = metadatas
        self._save()
        print(f"已加载 {len(documents)} 个历史用例到知识库")

    def retrieve_similar_cases(self, query: str, n_results: int = 3) -> list[str]:
        if not self.vectorizer or self.matrix is None:
            return []
        query_vec = self.vectorizer.transform([query])
        scores = cosine_similarity(query_vec, self.matrix).flatten()
        top_indices = np.argsort(scores)[::-1][:n_results]
        return [self.documents[i] for i in top_indices if scores[i] > 0]

    @property
    def case_count(self) -> int:
        return len(self.documents)

    def _save(self):
        os.makedirs(self.persist_dir, exist_ok=True)
        if self.vectorizer is None:
            return
        import pickle
        data = {
            "documents": self.documents,
            "ids": self.ids,
            "metadatas": self.metadatas,
        }
        with open(os.path.join(self.persist_dir, "data.json"), "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        with open(os.path.join(self.persist_dir, "vectorizer.pkl"), "wb") as f:
            pickle.dump(self.vectorizer, f)
        with open(os.path.join(self.persist_dir, "matrix.npy"), "wb") as f:
            np.save(f, self.matrix.toarray())

    def _load(self):
        vec_path = os.path.join(self.persist_dir, "vectorizer.pkl")
        if not os.path.exists(vec_path):
            return
        import pickle
        with open(os.path.join(self.persist_dir, "data.json"), "r", encoding="utf-8") as f:
            data = json.load(f)
        self.documents = data["documents"]
        self.ids = data["ids"]
        self.metadatas = data["metadatas"]
        with open(vec_path, "rb") as f:
            self.vectorizer = pickle.load(f)
        with open(os.path.join(self.persist_dir, "matrix.npy"), "rb") as f:
            self.matrix = np.load(f)