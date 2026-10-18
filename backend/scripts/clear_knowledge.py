from app.services.rag import collection

existing = collection.get()
ids = existing["ids"]
if ids:
    collection.delete(ids=ids)
print(f"Removed {len(ids)} chunks from the knowledge base.")