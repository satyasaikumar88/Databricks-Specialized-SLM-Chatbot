from __future__ import annotations

import json
from pathlib import Path

from sentence_transformers import SentenceTransformer
import faiss
import numpy as np


def index_documents(docs_path: str | Path, index_path: str | Path, model_name: str = 'sentence-transformers/all-MiniLM-L6-v2') -> None:
    docs_path = Path(docs_path)
    index_path = Path(index_path)
    index_path.parent.mkdir(parents=True, exist_ok=True)

    with docs_path.open('r', encoding='utf-8') as f:
        docs = json.load(f)

    model = SentenceTransformer(model_name)
    texts = [f"{doc.get('title', '')}: {doc.get('content', '')}" for doc in docs]
    embeddings = model.encode(texts, convert_to_numpy=True, normalize_embeddings=True)
    index = faiss.IndexFlatIP(embeddings.shape[1])
    index.add(embeddings.astype('float32'))
    faiss.write_index(index, str(index_path))
    print(f'Indexed {len(docs)} documents to {index_path}')


if __name__ == '__main__':
    index_documents('data/docs/databricks_docs.json', 'model/faiss_index.bin')
