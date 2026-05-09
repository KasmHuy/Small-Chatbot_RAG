import json
import os
import requests
import chromadb
from dotenv import load_dotenv

load_dotenv(r"D:\Small-Chatbot_RAG\.env")
API_KEY = os.getenv("GEMINI_API_KEY")

# Khởi tạo ChromaDB local
client = chromadb.PersistentClient(path=r"D:\Small-Chatbot_RAG\character-llm\data\vectordb")
collection = client.get_or_create_collection(name="ayaka_chunks")

def embed(text: str) -> list:
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-embedding-001:embedContent?key={API_KEY}"
    payload = {
        "model": "models/gemini-embedding-001",
        "content": {"parts": [{"text": text}]}
    }
    response = requests.post(url, json=payload)
    return response.json()["embedding"]["values"]

def build_index(chunks_path: str):
    """Embed toàn bộ chunks và lưu vào ChromaDB."""
    with open(chunks_path, encoding="utf-8") as f:
        chunks = json.load(f)

    print(f"Đang embed {len(chunks)} chunks...")
    for chunk in chunks:
        vector = embed(chunk["text"])
        collection.add(
            ids=[chunk["chunk_id"]],
            embeddings=[vector],
            documents=[chunk["text"]],
            metadatas=[{"section": chunk["section"]}]
        )
    print("Xong!")

def retrieve(question: str, top_k=3) -> str:
    """Tìm chunks liên quan nhất với câu hỏi."""
    vector = embed(question)
    results = collection.query(query_embeddings=[vector], n_results=top_k)
    return "\n\n".join(results["documents"][0])

if __name__ == "__main__":
    build_index(r"D:\Small-Chatbot_RAG\character-llm\data\processed\chunks.json")