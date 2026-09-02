import logging
from typing import List, Dict, Any, Optional
import chromadb
from chromadb.config import Settings as ChromaSettings
from app.config import settings

logger = logging.getLogger("ai_service.repositories.faq")

FAQ_KNOWLEDGE_BASE = [
    {
        "id": "faq_transfers_01",
        "topic": "Transfer Limits & Processing Times",
        "content": "Internal bank transfers are instant with zero fees. The daily transfer limit is $25,000 for standard accounts and $100,000 for verified premium accounts. External wire transfers may take 1-2 business days."
    },
    {
        "id": "faq_fees_02",
        "topic": "Account Maintenance Fees & Minimums",
        "content": "Our Standard Checking and Savings accounts have $0 monthly maintenance fees and zero minimum balance requirements. There are no overdraft fees for balances above -$50."
    },
    {
        "id": "faq_security_03",
        "topic": "Security & Fraud Protection",
        "content": "All accounts are protected with 256-bit encryption, continuous fraud monitoring, and FDIC insurance up to $250,000. If you suspect fraudulent activity, immediately freeze your account in settings or ask the AI assistant."
    },
    {
        "id": "faq_cards_04",
        "topic": "Debit & Virtual Cards",
        "content": "You can generate instant virtual cards for safe online shopping with custom spending limits. Physical debit cards are mailed within 3-5 business days upon request."
    },
    {
        "id": "faq_savings_05",
        "topic": "Interest Rates & High Yield Savings",
        "content": "Our High-Yield Savings Account currently offers a 4.75% APY with daily interest compounding and monthly payouts. There are no lockup periods or withdrawal penalties."
    },
    {
        "id": "faq_loans_06",
        "topic": "Personal Loans & Lines of Credit",
        "content": "Personal loans are available from $2,000 to $50,000 with competitive APRs starting at 6.49%. Approvals are processed within 24 hours with funds deposited directly into your checking account."
    },
    {
        "id": "faq_international_07",
        "topic": "International Payments & Currency Exchange",
        "content": "We support multi-currency balances in USD, EUR, GBP, and JPY with interbank exchange rates and a flat 0.3% FX fee. International SWIFT transfers arrive in 1-3 business days."
    }
]

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
            self.seed_knowledge_base()
        except Exception as e:
            logger.warning(f"Failed to connect to remote ChromaDB server: {e}. Falling back to in-memory EphemeralClient.")
            try:
                self.client = chromadb.EphemeralClient()
                self.collection = self.client.get_or_create_collection(
                    name=settings.CHROMA_COLLECTION,
                    metadata={"description": "Banking Knowledge Base & Policies"}
                )
                self.seed_knowledge_base()
            except Exception as inner_e:
                logger.error(f"Failed to initialize in-memory ChromaDB: {inner_e}")

    def seed_knowledge_base(self):
        if not self.collection:
            return
        
        try:
            existing_count = self.collection.count()
            if existing_count > 0:
                logger.info(f"ChromaDB collection '{settings.CHROMA_COLLECTION}' already has {existing_count} items.")
                return

            documents = [item["content"] for item in FAQ_KNOWLEDGE_BASE]
            metadatas = [{"topic": item["topic"]} for item in FAQ_KNOWLEDGE_BASE]
            ids = [item["id"] for item in FAQ_KNOWLEDGE_BASE]

            self.collection.add(
                documents=documents,
                metadatas=metadatas,
                ids=ids
            )
            logger.info(f"Successfully seeded {len(documents)} FAQ documents into ChromaDB.")
        except Exception as e:
            logger.error(f"Error seeding ChromaDB: {e}")

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
