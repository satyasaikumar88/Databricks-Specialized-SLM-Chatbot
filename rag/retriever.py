from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import faiss
import numpy as np
from sentence_transformers import SentenceTransformer


@dataclass
class RetrievalResult:
    id: str
    title: str
    source: str
    snippet: str
    score: float


class DocRetriever:
    def __init__(self, docs_path: str | Path, index_path: str | Path, embedding_model: str = 'sentence-transformers/all-MiniLM-L6-v2'):
        self.docs_path = Path(docs_path)
        self.index_path = Path(index_path)
        self.embedding_model = SentenceTransformer(embedding_model)
        self.documents = self._load_documents()
        self.index = self._load_or_build_index()

    def _load_documents(self) -> list[dict[str, Any]]:
        if not self.docs_path.exists():
            raise FileNotFoundError(f'Documents file not found: {self.docs_path}')

        with self.docs_path.open('r', encoding='utf-8') as f:
            docs = json.load(f)
        if not isinstance(docs, list):
            raise ValueError('The data file must define a list of documents.')
        return docs

    def _load_or_build_index(self) -> faiss.Index:
        if self.index_path.exists():
            return faiss.read_index(str(self.index_path))

        embeddings = self.embedding_model.encode([
            f"{doc.get('title', '')}: {doc.get('content', '')}" for doc in self.documents
        ], convert_to_numpy=True, normalize_embeddings=True)
        index = faiss.IndexFlatIP(embeddings.shape[1])
        index.add(embeddings.astype('float32'))
        faiss.write_index(index, str(self.index_path))
        return index

    def retrieve(self, query: str, top_k: int = 4) -> list[RetrievalResult]:
        query_vector = self.embedding_model.encode([query], convert_to_numpy=True, normalize_embeddings=True).astype('float32')
        scores, indices = self.index.search(query_vector, min(top_k, self.index.ntotal))

        results = []
        for score, idx in zip(scores[0], indices[0]):
            if idx < 0 or idx >= len(self.documents):
                continue
            doc = self.documents[int(idx)]
            snippet = doc.get('content', '')
            results.append(
                RetrievalResult(
                    id=str(doc.get('id', str(idx))),
                    title=str(doc.get('title', 'Databricks Doc')),
                    source=str(doc.get('source', '')), 
                    snippet=snippet[:500],
                    score=float(score),
                )
            )
        return results

    def build_index(self) -> None:
        embeddings = self.embedding_model.encode([
            f"{doc.get('title', '')}: {doc.get('content', '')}" for doc in self.documents
        ], convert_to_numpy=True, normalize_embeddings=True)
        index = faiss.IndexFlatIP(embeddings.shape[1])
        index.add(embeddings.astype('float32'))
        faiss.write_index(index, str(self.index_path))
        self.index = index

    def list_documents(self) -> list[dict[str, Any]]:
        return self.documents
