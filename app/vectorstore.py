from collections import defaultdict
from functools import lru_cache

from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings

from .config import CHROMA_DIR, EMBED_MODEL


@lru_cache(maxsize=1)
def get_store() -> Chroma:
    emb = HuggingFaceEmbeddings(model_name=EMBED_MODEL,
                                encode_kwargs={"normalize_embeddings": True})
    return Chroma(collection_name="eng_docs", embedding_function=emb,
                  persist_directory=str(CHROMA_DIR),
                  collection_metadata={"hnsw:space": "cosine"})


def add_chunks(chunks, source: str) -> None:
    store = get_store()
    store._collection.delete(where={"source": source})  # re-upload replaces old version
    if chunks:
        store.add_documents(chunks)


def list_documents() -> list[dict]:
    data = get_store().get(include=["metadatas"])
    agg = defaultdict(lambda: {"chunks": 0, "doc_id": ""})
    for m in data["metadatas"]:
        a = agg[m["source"]]
        a["chunks"] += 1
        a["doc_id"] = m["doc_id"]
    return [{"source": s, **v} for s, v in sorted(agg.items())]
