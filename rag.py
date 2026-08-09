"""
rag.py
Builds a FAISS vector index over the uploaded notes and answers
questions using retrieval-augmented generation via OpenRouter.

Flow:
  1. build_index(filepath)  -> chunks the doc, embeds it, saves FAISS index
  2. ask(question, index_id) -> retrieves top chunks, asks the model, returns
                                  answer + source page numbers
"""

import os
import pickle

import faiss
import numpy as np
from sentence_transformers import SentenceTransformer

from utils.extract import extract_text
from utils.openrouter_client import generate

INDEX_DIR = "summaries/indexes"
os.makedirs(INDEX_DIR, exist_ok=True)

_embedder = None


def get_embedder():
    global _embedder
    if _embedder is None:
        _embedder = SentenceTransformer("all-MiniLM-L6-v2")
    return _embedder


def _chunk_page(page_num, text, chunk_words=150, overlap=30):
    """Split a page's text into overlapping word chunks for better retrieval."""
    words = text.split()
    chunks = []
    step = chunk_words - overlap
    if step <= 0:
        step = chunk_words
    for i in range(0, len(words), step):
        chunk = " ".join(words[i:i + chunk_words])
        if chunk.strip():
            chunks.append((page_num, chunk))
        if i + chunk_words >= len(words):
            break
    return chunks


def build_index(filepath, doc_id):
    """Chunk + embed a document and persist a FAISS index for it."""
    pages = extract_text(filepath)
    chunks = []
    for page_num, text in pages:
        chunks.extend(_chunk_page(page_num, text))

    if not chunks:
        raise ValueError("No extractable text found in this document.")

    embedder = get_embedder()
    texts = [c[1] for c in chunks]
    vectors = embedder.encode(texts, convert_to_numpy=True, show_progress_bar=False)
    vectors = np.array(vectors, dtype="float32")

    index = faiss.IndexFlatL2(vectors.shape[1])
    index.add(vectors)

    faiss.write_index(index, os.path.join(INDEX_DIR, f"{doc_id}.index"))
    with open(os.path.join(INDEX_DIR, f"{doc_id}.meta"), "wb") as f:
        pickle.dump(chunks, f)

    return len(chunks)


def _load_index(doc_id):
    index_path = os.path.join(INDEX_DIR, f"{doc_id}.index")
    meta_path = os.path.join(INDEX_DIR, f"{doc_id}.meta")
    if not (os.path.exists(index_path) and os.path.exists(meta_path)):
        raise FileNotFoundError(
            f"No index found for doc_id={doc_id}. Upload and process the file first."
        )
    index = faiss.read_index(index_path)
    with open(meta_path, "rb") as f:
        chunks = pickle.load(f)
    return index, chunks


def delete_index(doc_id):
    """Remove the FAISS index + metadata for a document, if present."""
    index_path = os.path.join(INDEX_DIR, f"{doc_id}.index")
    meta_path = os.path.join(INDEX_DIR, f"{doc_id}.meta")
    for path in (index_path, meta_path):
        if os.path.exists(path):
            os.remove(path)


def ask(question, doc_id, top_k=4):
    """Retrieve the most relevant chunks for `question` and ask the model to answer."""
    index, chunks = _load_index(doc_id)
    embedder = get_embedder()

    q_vector = embedder.encode([question], convert_to_numpy=True)
    q_vector = np.array(q_vector, dtype="float32")

    distances, indices = index.search(q_vector, min(top_k, len(chunks)))
    retrieved = [chunks[i] for i in indices[0] if i != -1]

    context = "\n\n".join(f"[Page {p}]: {t}" for p, t in retrieved)
    source_pages = sorted({p for p, _ in retrieved})

    prompt = f"""You are a study assistant. Answer the student's question using
ONLY the context below. If the answer isn't in the context, say so honestly.

Context:
{context}

Question: {question}

Answer clearly and concisely, in a way a student can revise from."""

    answer = generate(prompt)
    return {"answer": answer, "source_pages": source_pages}
