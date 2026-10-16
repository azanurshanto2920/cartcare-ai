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


def search_context(query: str, n_results: int = 2) -> str:
    results = collection.query(query_texts=[query], n_results=n_results)
    if results["documents"] and results["documents"][0]:
        return "\n\n".join(results["documents"][0])
    return ""