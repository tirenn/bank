import logging
from typing import List, Dict, Any, Optional
import chromadb
from chromadb.config import Settings as ChromaSettings
from app.config import settings

logger = logging.getLogger("ai_service.repositories.faq")

class FAQRepository:
    def __init__(self):
        self.client = None
        self.collection = None
        self._init_chroma()

    def _init_chroma(self):
        try:
            logger.info(f"Connecting to ChromaDB at {settings.CHROMA_HOST}:{settings.CHROMA_PORT}")
            self.client = chromadb.HttpClient(
                host=settings.CHROMA_HOST,
                port=settings.CHROMA_PORT,
                settings=ChromaSettings(anonymized_telemetry=False)
            )
            self.collection = self.client.get_or_create_collection(
                name=settings.CHROMA_COLLECTION,
                metadata={"description": "Banking Knowledge Base & Policies"}
            )
        except Exception as e:
            logger.warning(f"Failed to connect to remote ChromaDB server: {e}. Falling back to in-memory EphemeralClient.")
            try:
                self.client = chromadb.EphemeralClient()
                self.collection = self.client.get_or_create_collection(
                    name=settings.CHROMA_COLLECTION,
                    metadata={"description": "Banking Knowledge Base & Policies"}
                )
            except Exception as inner_e:
                logger.error(f"Failed to initialize in-memory ChromaDB: {inner_e}")

    def add_document(self, topic: str, content: str, doc_id: Optional[str] = None) -> Dict[str, Any]:
        if not self.collection:
            raise RuntimeError("ChromaDB collection is not initialized.")

        import uuid
        actual_id = doc_id or f"doc_{uuid.uuid4().hex[:8]}"

        self.collection.upsert(
            documents=[content],
            metadatas=[{"topic": topic}],
            ids=[actual_id]
        )
        logger.info(f"Document added/updated in ChromaDB: id={actual_id}, topic='{topic}'")
        return {"id": actual_id, "topic": topic, "content": content}

    def ingest_document_atomic(
        self,
        topic: str,
        text: str,
        chunk_size: int = 500,
        overlap: int = 100,
        max_workers: int = 4
    ) -> Dict[str, Any]:
        if not self.collection:
            raise RuntimeError("ChromaDB collection is not initialized.")

        chunks = self.chunk_text(text, chunk_size=chunk_size, overlap=overlap)
        if not chunks:
            raise ValueError("Document contains no valid text content to chunk.")

        import uuid
        import concurrent.futures
        import time

        batch_id = f"batch_{uuid.uuid4().hex[:8]}"
        inserted_ids = []
        errors = []

        chunk_tasks = []
        for i, chunk in enumerate(chunks):
            chunk_id = f"{batch_id}_chunk_{i+1:03d}"
            metadata = {
                "topic": topic,
                "batch_id": batch_id,
                "chunk_index": i + 1,
                "total_chunks": len(chunks),
                "created_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
            }
            chunk_tasks.append((chunk_id, chunk, metadata))

        def insert_worker(task):
            cid, ctext, cmet = task
            try:
                self.collection.upsert(
                    documents=[ctext],
                    metadatas=[cmet],
                    ids=[cid]
                )
                return cid, None
            except Exception as exc:
                return cid, exc

        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_chunk = {executor.submit(insert_worker, task): task for task in chunk_tasks}
            for future in concurrent.futures.as_completed(future_to_chunk):
                cid, err = future.result()
                if err:
                    errors.append((cid, err))
                else:
                    inserted_ids.append(cid)

        # Atomic Rollback on Failure
        if errors:
            logger.error(f"Atomic ingestion failed for topic '{topic}' with {len(errors)} errors. Executing full rollback of {len(inserted_ids)} chunks...")
            if inserted_ids:
                try:
                    self.collection.delete(ids=inserted_ids)
                    logger.info(f"Rollback successful. Deleted {len(inserted_ids)} partial chunks for batch {batch_id}.")
                except Exception as rollback_err:
                    logger.critical(f"Critical error during ChromaDB rollback: {rollback_err}")
            
            first_err = errors[0][1]
            raise RuntimeError(f"Atomic ingestion transaction failed: {first_err}. All {len(inserted_ids)} chunks have been rolled back.")

        logger.info(f"Atomic parallel ingestion succeeded: topic='{topic}', batch_id={batch_id}, chunks={len(chunks)}")
        return {
            "batch_id": batch_id,
            "topic": topic,
            "total_chunks": len(chunks),
            "chunk_ids": inserted_ids,
            "char_count": len(text),
            "status": "COMMITTED"
        }

    def ingest_custom_chunks_atomic(
        self,
        topic: str,
        chunks: List[Dict[str, Any]],
        max_workers: int = 4
    ) -> Dict[str, Any]:
        """
        Ingests pre-computed semantic chunks (e.g. from LLM Dynamic Chunking).
        Enforces ALL-OR-NOTHING atomic transaction with automatic rollback on error.
        """
        if not self.collection:
            raise RuntimeError("ChromaDB collection is not initialized.")

        if not chunks:
            raise ValueError("No semantic chunks provided for ingestion.")

        import uuid
        import concurrent.futures
        import time

        batch_id = f"batch_{uuid.uuid4().hex[:8]}"
        inserted_ids = []
        errors = []

        chunk_tasks = []
        total_chars = 0
        for i, chunk_data in enumerate(chunks):
            chunk_content = chunk_data.get("content", "").strip() if isinstance(chunk_data, dict) else str(chunk_data).strip()
            if not chunk_content:
                continue
            total_chars += len(chunk_content)
            chunk_id = f"{batch_id}_chunk_{i+1:03d}"
            metadata = {
                "topic": topic,
                "batch_id": batch_id,
                "chunk_index": i + 1,
                "total_chunks": len(chunks),
                "strategy": chunk_data.get("strategy", "llm_dynamic") if isinstance(chunk_data, dict) else "llm_dynamic",
                "model": chunk_data.get("model", "llm") if isinstance(chunk_data, dict) else "llm",
                "created_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
            }
            chunk_tasks.append((chunk_id, chunk_content, metadata))

        def insert_worker(task):
            cid, ctext, cmet = task
            try:
                self.collection.upsert(
                    documents=[ctext],
                    metadatas=[cmet],
                    ids=[cid]
                )
                return cid, None
            except Exception as exc:
                return cid, exc

        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_chunk = {executor.submit(insert_worker, task): task for task in chunk_tasks}
            for future in concurrent.futures.as_completed(future_to_chunk):
                cid, err = future.result()
                if err:
                    errors.append((cid, err))
                else:
                    inserted_ids.append(cid)

        if errors:
            logger.error(f"Atomic ingestion failed for topic '{topic}' with {len(errors)} errors. Rolling back {len(inserted_ids)} chunks...")
            if inserted_ids:
                try:
                    self.collection.delete(ids=inserted_ids)
                    logger.info(f"Rollback successful. Deleted {len(inserted_ids)} chunks for batch {batch_id}.")
                except Exception as rollback_err:
                    logger.critical(f"Critical error during ChromaDB rollback: {rollback_err}")
            
            first_err = errors[0][1]
            raise RuntimeError(f"Atomic custom chunk ingestion failed: {first_err}")

        logger.info(f"Atomic custom chunk ingestion succeeded: topic='{topic}', batch_id={batch_id}, chunks={len(chunk_tasks)}")
        return {
            "batch_id": batch_id,
            "topic": topic,
            "total_chunks": len(chunk_tasks),
            "chunk_ids": inserted_ids,
            "char_count": total_chars,
            "strategy": "llm_dynamic",
            "status": "COMMITTED"
        }


    @staticmethod
    def chunk_text(text: str, chunk_size: int = 500, overlap: int = 100) -> List[str]:
        if not text:
            return []
        
        clean_text = " ".join(text.split())
        chunks = []
        start = 0
        text_len = len(clean_text)

        while start < text_len:
            end = min(start + chunk_size, text_len)
            chunk = clean_text[start:end].strip()
            if chunk:
                chunks.append(chunk)
            if end == text_len:
                break
            start += max(1, chunk_size - overlap)

        return chunks

    def list_documents(self) -> List[Dict[str, Any]]:
        if not self.collection:
            return []

        try:
            data = self.collection.get()
            docs = []
            if data and "ids" in data:
                for i in range(len(data["ids"])):
                    docs.append({
                        "id": data["ids"][i],
                        "topic": data["metadatas"][i].get("topic", "") if data.get("metadatas") else "",
                        "batch_id": data["metadatas"][i].get("batch_id", "") if data.get("metadatas") else "",
                        "chunk_index": data["metadatas"][i].get("chunk_index", 1) if data.get("metadatas") else 1,
                        "content": data["documents"][i] if data.get("documents") else "",
                    })
            return docs
        except Exception as e:
            logger.error(f"Error listing documents from ChromaDB: {e}")
            return []

    def delete_document(self, doc_id: str) -> bool:
        if not self.collection:
            return False

        try:
            self.collection.delete(ids=[doc_id])
            logger.info(f"Document deleted from ChromaDB: id={doc_id}")
            return True
        except Exception as e:
            logger.error(f"Error deleting document {doc_id}: {e}")
            return False

    def delete_batch(self, batch_id: str) -> int:
        if not self.collection:
            return 0
        try:
            results = self.collection.get(where={"batch_id": batch_id})
            ids_to_del = results.get("ids", [])
            if ids_to_del:
                self.collection.delete(ids=ids_to_del)
                logger.info(f"Deleted batch {batch_id} ({len(ids_to_del)} chunks)")
                return len(ids_to_del)
            return 0
        except Exception as e:
            logger.error(f"Error deleting batch {batch_id}: {e}")
            return 0

    def search_raw(self, query: str, n_results: int = 10) -> List[Dict[str, Any]]:
        """
        Executes raw vector query against ChromaDB returning structured chunk dicts.
        Used by the Hybrid RAG pipeline for Reciprocal Rank Fusion.
        """
        if not self.collection:
            return []

        try:
            results = self.collection.query(
                query_texts=[query],
                n_results=n_results
            )
            docs = results.get("documents", [[]])[0]
            ids = results.get("ids", [[]])[0] if results.get("ids") else []
            metadatas = results.get("metadatas", [[]])[0] if results.get("metadatas") else []
            distances = results.get("distances", [[]])[0] if results.get("distances") else []

            items = []
            for i in range(len(docs)):
                items.append({
                    "id": ids[i] if i < len(ids) else f"doc_{i}",
                    "document": docs[i],
                    "metadata": metadatas[i] if i < len(metadatas) and metadatas[i] else {},
                    "distance": distances[i] if i < len(distances) else None,
                })
            return items
        except Exception as e:
            logger.error(f"Error searching ChromaDB search_raw: {e}")
            return []

    def search(self, query: str, n_results: int = 3) -> str:
        if not self.collection:
            return "Knowledge base currently unavailable."

        try:
            results = self.collection.query(
                query_texts=[query],
                n_results=n_results
            )
            docs = results.get("documents", [[]])[0]
            if not docs:
                return "No matching banking policy or FAQ found."
            
            return "\n\n".join([f"• {doc}" for doc in docs])
        except Exception as e:
            logger.error(f"Error searching ChromaDB: {e}")
            return f"Error querying knowledge base: {str(e)}"

faq_repository = FAQRepository()
