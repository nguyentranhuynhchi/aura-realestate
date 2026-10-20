import os
import chromadb
from chromadb.utils import embedding_functions

def sync_to_chroma(chunks: list[dict], collection_name: str = "realestate_collection") -> dict:
    """Đồng bộ hóa các chunks và metadata tương ứng vào ChromaDB Vector Database."""
    if not chunks:
        return {"status": "skipped", "synced_count": 0, "reason": "empty_chunks"}
    
    host = os.getenv("CHROMA_HOST", "localhost")
    port = int(os.getenv("CHROMA_PORT", 8001))
    
    try:
        client = chromadb.HttpClient(host=host, port=port)
        ef = embedding_functions.SentenceTransformerEmbeddingFunction(model_name="all-MiniLM-L6-v2")
        collection = client.get_or_create_collection(name=collection_name, embedding_function=ef)
        
        ids = [str(c["id"]) for c in chunks]
        documents = [c["text"] for c in chunks]
        metadatas = [c["metadata"] for c in chunks]
        
        collection.upsert(ids=ids, documents=documents, metadatas=metadatas)
        return {"status": "success", "synced_count": len(chunks), "collection": collection_name}
    except Exception as e:
        return {"status": "error", "synced_count": 0, "error_msg": str(e)}

if __name__ == "__main__":
    dummy = [{"id": "dummy_1", "text": "Test BĐS Quận 1", "metadata": {"price": 5.0, "address": "Quận 1"}}]
    print(sync_to_chroma(dummy))
