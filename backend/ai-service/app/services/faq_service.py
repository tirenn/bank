import io
import logging
from typing import List, Dict, Any, Optional
from pypdf import PdfReader
from openai import AsyncOpenAI
from app.repositories.faq_repository import faq_repository
from app.services.model_fallback import model_fallback
from app.services.rag_cache_service import rag_cache_service
from app.services.bm25_service import bm25_service
from app.config import settings


logger = logging.getLogger("ai_service.services.faq")

class FAQService:
    def __init__(self, repo=faq_repository):
        self.repo = repo

    def list_documents(self) -> List[Dict[str, Any]]:
        return self.repo.list_documents()

    async def ingest_text_atomic(
        self,
        topic: str,
        content: str,
        chunk_size: int = 500,
        overlap: int = 100,
        use_llm_chunking: bool = True,
        api_key_override: Optional[str] = None,
        model_override: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Ingests text with LLM-Driven Dynamic Semantic Chunking first.
        If LLM is unavailable or yields empty, automatically falls back to deterministic sliding-window chunking.
        """
        api_key = api_key_override or settings.OPENROUTER_API_KEY
        openai_client = None
        if use_llm_chunking and api_key and api_key.strip() and api_key != "YOUR_OPENROUTER_API_KEY_HERE":
            try:
                openai_client = AsyncOpenAI(
                    base_url="https://openrouter.ai/api/v1",
                    api_key=api_key.strip(),
                    default_headers={
                        "HTTP-Referer": "http://localhost:5173",
                        "X-Title": "Antigravity Bank AI Dynamic RAG",
                    }
                )
            except Exception as e:
                logger.warning(f"Failed to initialize OpenAI client for dynamic chunking: {e}")

        # 1. Try LLM Dynamic Semantic Chunking with multi-model fallback
        if openai_client:
            try:
                semantic_chunks = await model_fallback.execute_dynamic_chunking(
                    openai_client=openai_client,
                    topic=topic,
                    text=content,
                    model_override=model_override
                )
                if semantic_chunks:
                    res = self.repo.ingest_custom_chunks_atomic(topic=topic, chunks=semantic_chunks)
                    await rag_cache_service.invalidate_all()
                    await bm25_service.sync_from_faq_repository()
                    return res
            except Exception as llm_err:
                logger.warning(f"LLM Dynamic Chunking encountered error: {llm_err}. Falling back to sliding-window chunker.")


        # 2. Deterministic Sliding Window Fallback
        res = self.repo.ingest_document_atomic(
            topic=topic,
            text=content,
            chunk_size=chunk_size,
            overlap=overlap
        )
        await rag_cache_service.invalidate_all()
        await bm25_service.sync_from_faq_repository()
        return res


    def extract_pdf_in_memory(self, pdf_bytes: bytes) -> str:
        try:
            reader = PdfReader(io.BytesIO(pdf_bytes))
            extracted_pages = []
            for idx, page in enumerate(reader.pages):
                page_str = page.extract_text()
                if page_str and page_str.strip():
                    extracted_pages.append(f"--- Page {idx + 1} ---\n" + page_str.strip())
            
            if not extracted_pages:
                raise ValueError("PDF document contains no extractable text.")

            return "\n\n".join(extracted_pages)
        except Exception as e:
            raise ValueError(f"Failed to parse PDF document in-memory: {str(e)}")

    async def ingest_file_stream(
        self,
        filename: str,
        file_bytes: bytes,
        topic: str,
        chunk_size: int = 500,
        overlap: int = 100,
        use_llm_chunking: bool = True,
        api_key_override: Optional[str] = None,
        model_override: Optional[str] = None
    ) -> Dict[str, Any]:
        if filename.lower().endswith(".pdf"):
            logger.info(f"Extracting PDF text in-memory from '{filename}' ({len(file_bytes)} bytes)...")
            text_content = self.extract_pdf_in_memory(file_bytes)
        else:
            text_content = file_bytes.decode("utf-8", errors="replace")

        if not text_content.strip():
            raise ValueError("Document yielded no valid text content.")

        return await self.ingest_text_atomic(
            topic=topic,
            content=text_content,
            chunk_size=chunk_size,
            overlap=overlap,
            use_llm_chunking=use_llm_chunking,
            api_key_override=api_key_override,
            model_override=model_override
        )

    async def delete_document(self, doc_id: str) -> bool:
        res = self.repo.delete_document(doc_id)
        if res:
            await rag_cache_service.invalidate_all()
            await bm25_service.sync_from_faq_repository()
        return res

    async def delete_batch(self, batch_id: str) -> int:
        count = self.repo.delete_batch(batch_id)
        if count > 0:
            await rag_cache_service.invalidate_all()
            await bm25_service.sync_from_faq_repository()
        return count


faq_service = FAQService()



