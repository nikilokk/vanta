# core/vector_memory.py
import uuid
from datetime import datetime
from pathlib import Path

import chromadb
from chromadb.config import Settings
from ollama import embed

from config import DATA_DIR
from core.logger import get_logger

logger = get_logger(__name__)

# === НАСТРОЙКИ ===
CHROMA_DIR = DATA_DIR / "chroma_db"
CHROMA_DIR.mkdir(exist_ok=True)

EMBED_MODEL = "bge-m3"          # или "qllama/bge-m3"
COLLECTION_NAME = "vanta_conversations"
SIMILARITY_THRESHOLD = 1.2      # отсекаем нерелевантные результаты

_client = None
_collection = None


def _get_collection():
    """Ленивая инициализация коллекции ChromaDB."""
    global _client, _collection
    if _collection is not None:
        return _collection

    _client = chromadb.PersistentClient(
        path=str(CHROMA_DIR),
        settings=Settings(anonymized_telemetry=False),
    )
    _collection = _client.get_or_create_collection(
        name=COLLECTION_NAME,
        metadata={"hnsw:space": "cosine"},
    )
    logger.info(f"VectorMemory: коллекция '{COLLECTION_NAME}' готова")
    return _collection


def _embed_texts(texts: list) -> list:
    """Превращает список текстов в векторы через Ollama."""
    try:
        response = embed(model=EMBED_MODEL, input=texts)
        return response["embeddings"]
    except Exception as e:
        logger.error(f"VectorMemory: ошибка эмбеддинга: {e}")
        return []


def save_conversation(user_message: str, assistant_response: str):
    """Сохраняет пару сообщение-ответ в векторную память."""
    collection = _get_collection()
    if collection is None:
        return {"success": False, "error": "ChromaDB недоступна"}

    # Формируем текст для запоминания
    text = f"Пользователь: {user_message}\nVanta: {assistant_response}"

    # Считаем эмбеддинг
    embeddings = _embed_texts([text])
    if not embeddings:
        return {"success": False, "error": "Не удалось создать эмбеддинг"}

    doc_id = f"conv_{uuid.uuid4().hex[:12]}"

    try:
        collection.add(
            ids=[doc_id],
            embeddings=embeddings,
            documents=[text],
            metadatas=[{
                "timestamp": datetime.now().isoformat(),
                "user_message": user_message[:500],  # обрезаем для метаданных
            }],
        )
        logger.info(f"VectorMemory: сохранён диалог {doc_id}")
        return {"success": True, "id": doc_id}
    except Exception as e:
        logger.error(f"VectorMemory: ошибка сохранения: {e}")
        return {"success": False, "error": str(e)}


def search_conversations(query: str, n_results: int = 3):
    """Ищет релевантные диалоги по смыслу."""
    collection = _get_collection()
    if collection is None:
        return {"success": False, "error": "ChromaDB недоступна", "results": []}

    embeddings = _embed_texts([query])
    if not embeddings:
        return {"success": False, "error": "Не удалось создать эмбеддинг", "results": []}

    try:
        results = collection.query(
            query_embeddings=embeddings,
            n_results=n_results,
            include=["documents", "metadatas", "distances"],
        )

        # Фильтруем по порогу расстояния
        filtered = []
        for i, doc in enumerate(results["documents"][0]):
            distance = results["distances"][0][i]
            if distance <= SIMILARITY_THRESHOLD:
                filtered.append({
                    "text": doc,
                    "distance": round(distance, 3),
                    "timestamp": results["metadatas"][0][i].get("timestamp", "?"),
                })

        return {"success": True, "results": filtered}
    except Exception as e:
        logger.error(f"VectorMemory: ошибка поиска: {e}")
        return {"success": False, "error": str(e), "results": []}


def get_stats():
    """Статистика по векторной памяти."""
    collection = _get_collection()
    if collection is None:
        return {"success": False, "error": "ChromaDB недоступна"}
    try:
        count = collection.count()
        return {"success": True, "total_conversations": count}
    except Exception as e:
        return {"success": False, "error": str(e)}