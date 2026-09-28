"""
Local, on-disk vector database (Chroma) holding one embedding per candidate
"chunk" (overview / work history / skills / projects - see
crud.candidate_to_rag_documents). We compute embeddings ourselves via Gemini
and hand Chroma the finished vectors, so Chroma is doing pure storage +
similarity search, nothing else.
"""
import chromadb
from app.config import CHROMA_DIR
from app.gemini_client import embed_texts

_client = None
_collection = None

COLLECTION_NAME = "candidates"


def get_collection():
    global _client, _collection
    if _collection is None:
        _client = chromadb.PersistentClient(path=str(CHROMA_DIR))
        _collection = _client.get_or_create_collection(COLLECTION_NAME)
    return _collection


def remove_candidate(candidate_id: int):
    collection = get_collection()
    try:
        collection.delete(where={"candidate_id": candidate_id})
    except Exception:
        pass


def index_candidate(candidate_id: int, candidate_name: str, source_files: str, documents: list[dict]):
    """Replace all vector chunks for a candidate with a fresh set. Call this after
    any create/update so the chatbot always reflects the latest database state."""
    remove_candidate(candidate_id)
    if not documents:
        return
    collection = get_collection()
    texts = [d["text"] for d in documents]
    embeddings = embed_texts(texts, task_type="RETRIEVAL_DOCUMENT")
    ids = [f"cand-{candidate_id}-{d['chunk_type']}" for d in documents]
    metadatas = [
        {
            "candidate_id": candidate_id,
            "candidate_name": candidate_name,
            "chunk_type": d["chunk_type"],
            "source_files": source_files or "",
        }
        for d in documents
    ]
    collection.add(ids=ids, embeddings=embeddings, documents=texts, metadatas=metadatas)


def search(query: str, top_k: int = 8):
    collection = get_collection()
    if collection.count() == 0:
        return []
    query_embedding = embed_texts([query], task_type="RETRIEVAL_QUERY")[0]
    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=min(top_k, collection.count()),
    )
    hits = []
    for doc, meta, distance in zip(results["documents"][0], results["metadatas"][0], results["distances"][0]):
        hits.append({"text": doc, "metadata": meta, "distance": distance})
    return hits
