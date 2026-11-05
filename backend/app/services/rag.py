import chromadb
from pypdf import PdfReader

from app.core.config import settings

chroma_client = chromadb.PersistentClient(path=settings.chroma_path)
collection = chroma_client.get_or_create_collection(name="knowledge_base")


def chunk_text(text: str, chunk_size: int = 500, overlap: int = 50) -> list[str]:
    chunks = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunks.append(text[start:end])
        start += chunk_size - overlap
    return chunks


def extract_pdf_text(path: str) -> str:
    reader = PdfReader(path)
    pages = [(page.extract_text() or "") for page in reader.pages]
    return "\n".join(pages)


def index_chunks(chunks: list[str]) -> int:
    # Simple approach for now: replace everything with the new document.
    existing = collection.get()
    if existing["ids"]:
        collection.delete(ids=existing["ids"])

    if not chunks:
        return 0

    collection.add(
        documents=chunks,
        ids=[f"chunk_{i}" for i in range(len(chunks))],
    )
    return len(chunks)


MAX_DISTANCE = 1.45  # lower means a closer match; chunks farther than this are ignored
MIN_RESULTS = 2  # the closest chunks are always returned, even when none is a close match


def search_context(query: str, n_results: int = 4) -> str:
    results = collection.query(query_texts=[query], n_results=n_results)
    documents = results["documents"][0] if results["documents"] else []
    distances = results["distances"][0] if results["distances"] else []

    pairs = list(zip(documents, distances))
    chosen = [doc for doc, dist in pairs if dist <= MAX_DISTANCE]
    if len(chosen) < MIN_RESULTS:
        chosen = [doc for doc, _ in pairs[:MIN_RESULTS]]
    return "\n\n".join(chosen)


def index_document(source: str, chunks: list[str]) -> int:
    # Uploading a file with the same name replaces its old chunks
    collection.delete(where={"source": source})

    if not chunks:
        return 0

    collection.add(
        documents=chunks,
        ids=[f"{source}::{i}" for i in range(len(chunks))],
        metadatas=[{"source": source} for _ in chunks],
    )
    return len(chunks)


def list_documents() -> list[dict]:
    data = collection.get(include=["metadatas"])
    counts: dict[str, int] = {}
    for meta in data["metadatas"] or []:
        name = (meta or {}).get("source")
        if name:
            counts[name] = counts.get(name, 0) + 1
    return [{"source": name, "chunks": count} for name, count in sorted(counts.items())]


def delete_document(source: str) -> int:
    existing = collection.get(where={"source": source})
    count = len(existing["ids"])
    if count:
        collection.delete(ids=existing["ids"])
    return count