# -*- coding: utf-8 -*-
"""
RAG 知识库
向量存储、检索、增强生成
"""

import json
from pathlib import Path
from typing import Optional

from config import DATA_DIR

try:
    import chromadb
    from chromadb.config import Settings
    CHROMADB_AVAILABLE = True
except ImportError:
    CHROMADB_AVAILABLE = False


class RAGKnowledgeBase:
    """RAG 知识库"""

    COLLECTION_NAME = "marketing_knowledge"

    def __init__(self, persist_dir: Optional[Path] = None):
        self.persist_dir = Path(persist_dir or DATA_DIR / "rag_chroma")
        self.persist_dir.mkdir(parents=True, exist_ok=True)
        self._client = None
        self._collection = None

    def _get_client(self):
        if not CHROMADB_AVAILABLE:
            return None
        if self._client is None:
            self._client = chromadb.PersistentClient(
                path=str(self.persist_dir),
                settings=Settings(anonymized_telemetry=False),
            )
        return self._client

    def _get_collection(self):
        if self._collection is None and self._get_client():
            self._collection = self._client.get_or_create_collection(
                self.COLLECTION_NAME,
                metadata={"description": "营销知识库：爆款模型、创意拆解"},
            )
        return self._collection

    def add_documents(self, docs: list[dict]) -> int:
        """
        添加文档到知识库
        docs: [{"id": str, "content": str, "metadata": dict}, ...]
        """
        coll = self._get_collection()
        if not coll:
            return 0
        ids = [d.get("id", f"doc_{i}") for i, d in enumerate(docs)]
        contents = [d.get("content", "") for d in docs]
        metadatas = [d.get("metadata", {}) for d in docs]
        coll.add(ids=ids, documents=contents, metadatas=metadatas)
        return len(docs)

    def retrieve(self, query: str, top_k: int = 5) -> list[dict]:
        """
        检索相关文档
        返回: [{"content": str, "metadata": dict, "distance": float}, ...]
        """
        coll = self._get_collection()
        if not coll:
            return []
        result = coll.query(query_texts=[query], n_results=top_k)
        if not result or not result.get("documents"):
            return []
        out = []
        for i, doc in enumerate(result["documents"][0] or []):
            meta = (result.get("metadatas") or [[]])[0][i] if result.get("metadatas") else {}
            dist = (result.get("distances") or [[]])[0][i] if result.get("distances") else 0
            out.append({"content": doc, "metadata": meta or {}, "distance": dist})
        return out

    def retrieve_for_prompt(self, query: str, top_k: int = 3) -> str:
        """检索并格式化为 prompt 上下文"""
        docs = self.retrieve(query, top_k=top_k)
        if not docs:
            return ""
        parts = ["【知识库参考】"]
        for i, d in enumerate(docs, 1):
            parts.append(f"{i}. {d['content'][:500]}...")
        return "\n".join(parts)

    def sync_from_viral_library(self) -> int:
        """从爆款内容库同步到 RAG"""
        try:
            viral_dir = DATA_DIR / "knowledge" / "viral_models"
            decon_dir = DATA_DIR / "knowledge" / "deconstructions"
        except Exception:
            return 0
        docs = []
        for f in (viral_dir.glob("*.json") if viral_dir.exists() else []):
            try:
                with open(f, "r", encoding="utf-8") as fp:
                    data = json.load(fp)
                content = json.dumps(data, ensure_ascii=False)
                docs.append({
                    "id": f"viral_{f.stem}",
                    "content": content,
                    "metadata": {"type": "viral_model", "source": str(f.name)},
                })
            except Exception:
                pass
        for f in (decon_dir.glob("*.json") if decon_dir.exists() else []):
            try:
                with open(f, "r", encoding="utf-8") as fp:
                    data = json.load(fp)
                content = json.dumps(data, ensure_ascii=False)
                docs.append({
                    "id": f"decon_{f.stem}",
                    "content": content,
                    "metadata": {"type": "deconstruction", "source": str(f.name)},
                })
            except Exception:
                pass
        if docs:
            try:
                client = self._get_client()
                if client:
                    try:
                        client.delete_collection(self.COLLECTION_NAME)
                    except Exception:
                        pass
                    self._collection = None
            except Exception:
                pass
            return self.add_documents(docs)
        return 0

    def is_available(self) -> bool:
        return CHROMADB_AVAILABLE and self._get_collection() is not None
