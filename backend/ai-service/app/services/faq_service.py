import io
import logging
from typing import List, Dict, Any
from pypdf import PdfReader
from app.repositories.faq_repository import faq_repository

logger = logging.getLogger("ai_service.services.faq")

class FAQService:
    def __init__(self, repo=faq_repository):
        self.repo = repo

    def list_documents(self) -> List[Dict[str, Any]]:
        return self.repo.list_documents()

    def ingest_text_atomic(self, topic: str, content: str, chunk_size: int = 500, overlap: int = 100) -> Dict[str, Any]:
        return self.repo.ingest_document_atomic(
            topic=topic,
            text=content,
            chunk_size=chunk_size,
            overlap=overlap
        )

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

    def ingest_file_stream(self, filename: str, file_bytes: bytes, topic: str, chunk_size: int = 500, overlap: int = 100) -> Dict[str, Any]:
        if filename.lower().endswith(".pdf"):
            logger.info(f"Extracting PDF text in-memory from '{filename}' ({len(file_bytes)} bytes)...")
            text_content = self.extract_pdf_in_memory(file_bytes)
        else:
            text_content = file_bytes.decode("utf-8", errors="replace")

        if not text_content.strip():
            raise ValueError("Document yielded no valid text content.")

        return self.ingest_text_atomic(
            topic=topic,
            content=text_content,
            chunk_size=chunk_size,
            overlap=overlap
        )

    def delete_document(self, doc_id: str) -> bool:
        return self.repo.delete_document(doc_id)

    def delete_batch(self, batch_id: str) -> int:
        return self.repo.delete_batch(batch_id)

    def seed(self):
        self.repo.seed_knowledge_base()

faq_service = FAQService()
