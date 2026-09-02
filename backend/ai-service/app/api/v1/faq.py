import logging
from fastapi import APIRouter, HTTPException, Depends, UploadFile, File, Form
from app.domain.schemas import DocumentUploadRequest, AtomicIngestResponse
from app.api.dependencies import require_admin_role
from app.services.faq_service import faq_service

logger = logging.getLogger("ai_service.api.faq")

router = APIRouter(prefix="/ai/faq", tags=["RAG Knowledge Base"])

@router.get("")
async def get_faq_documents():
    """Retrieve all indexed documents/chunks from ChromaDB RAG."""
    docs = faq_service.list_documents()
    return {
        "total_documents": len(docs),
        "documents": docs
    }

@router.post("/upload", response_model=AtomicIngestResponse)
async def upload_faq_document(
    req: DocumentUploadRequest,
    admin_user: dict = Depends(require_admin_role)
):
    """
    Ingests text into ChromaDB using PARALLEL CHUNKING and ATOMIC ALL-OR-NOTHING transaction.
    If any chunk fails, all inserted chunks are immediately rolled back.
    Requires ADMIN role.
    """
    if not req.topic.strip() or not req.content.strip():
        raise HTTPException(status_code=400, detail="Topic and content cannot be empty.")
    
    try:
        res = await faq_service.ingest_text_atomic(
            topic=req.topic.strip(),
            content=req.content.strip(),
            chunk_size=req.chunk_size or 500,
            overlap=req.overlap or 100
        )
        return AtomicIngestResponse(
            message=f"Successfully indexed document with {res['total_chunks']} chunks in parallel ({res.get('strategy', 'sliding_window')}).",
            batch_id=res["batch_id"],
            topic=res["topic"],
            total_chunks=res["total_chunks"],
            char_count=res["char_count"],
            status="COMMITTED"
        )
    except Exception as e:
        logger.error(f"Atomic ingestion failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/upload-file", response_model=AtomicIngestResponse)
async def upload_faq_file(
    topic: str = Form(..., description="Document topic or category"),
    chunk_size: int = Form(500, description="Sliding window chunk character size"),
    overlap: int = Form(100, description="Chunk overlap character count"),
    file: UploadFile = File(..., description="PDF or text file (processed 100% in-memory without disk storage)"),
    admin_user: dict = Depends(require_admin_role)
):
    """
    ZERO-FILE-STORAGE INGESTION:
    Reads uploaded PDF or TXT directly from RAM memory byte-stream.
    Extracts text in-memory, chunks in parallel, and indexes atomically into ChromaDB.
    No file is ever saved to the server's filesystem.
    Requires ADMIN role.
    """
    if not topic.strip():
        raise HTTPException(status_code=400, detail="Topic cannot be empty.")

    filename = (file.filename or "").lower()
    file_bytes = await file.read()
    if not file_bytes:
        raise HTTPException(status_code=400, detail="Uploaded file is empty.")

    try:
        res = await faq_service.ingest_file_stream(
            filename=filename,
            file_bytes=file_bytes,
            topic=topic.strip(),
            chunk_size=chunk_size,
            overlap=overlap
        )
        return AtomicIngestResponse(
            message=f"File '{file.filename}' parsed in-memory and indexed with {res['total_chunks']} chunks ({res.get('strategy', 'sliding_window')}).",
            batch_id=res["batch_id"],
            topic=res["topic"],
            total_chunks=res["total_chunks"],
            char_count=res["char_count"],
            status="COMMITTED"
        )
    except Exception as e:
        logger.error(f"Atomic file ingestion failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        del file_bytes


@router.delete("/{doc_id}")
async def delete_faq_document(
    doc_id: str,
    admin_user: dict = Depends(require_admin_role)
):
    """Delete a single chunk/document from ChromaDB RAG. Requires ADMIN role."""
    success = await faq_service.delete_document(doc_id)
    if not success:
        raise HTTPException(status_code=404, detail="Document ID not found or could not be deleted.")
    return {"message": f"Document {doc_id} deleted successfully."}

@router.delete("/batch/{batch_id}")
async def delete_faq_batch(
    batch_id: str,
    admin_user: dict = Depends(require_admin_role)
):
    """Delete all chunks belonging to a specific batch from ChromaDB RAG. Requires ADMIN role."""
    count = await faq_service.delete_batch(batch_id)
    if count == 0:
        raise HTTPException(status_code=404, detail=f"No chunks found for batch ID {batch_id}.")
    return {"message": f"Successfully deleted batch {batch_id} ({count} chunks removed)."}

