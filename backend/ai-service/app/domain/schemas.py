from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field

class ChatMessage(BaseModel):
    role: str = Field(..., description="Role: 'user', 'assistant', or 'system'")
    content: str = Field(..., description="Content of the message")

class ChatRequest(BaseModel):
    messages: List[ChatMessage]
    openrouter_api_key: Optional[str] = Field(None, description="Optional OpenRouter API key override")
    model: Optional[str] = Field(None, description="Optional Model override")

class ChatResponse(BaseModel):
    reply: str
    action_type: Optional[str] = None
    action_data: Optional[Dict[str, Any]] = None
    tools_used: Optional[List[str]] = []

class DocumentUploadRequest(BaseModel):
    topic: str = Field(..., description="Category or topic of the document")
    content: str = Field(..., description="Raw text content to ingest into vector knowledge base")
    chunk_size: Optional[int] = Field(500, description="Character count per sliding window chunk")
    overlap: Optional[int] = Field(100, description="Character overlap between adjacent chunks")

class AtomicIngestResponse(BaseModel):
    message: str
    batch_id: str
    topic: str
    total_chunks: int
    char_count: int
    status: str = "COMMITTED"
