from fastapi import APIRouter, Header, HTTPException, Request
from app.domain.schemas import ChatRequest, ChatResponse
from app.services.agent_service import agent_service

router = APIRouter(prefix="/ai", tags=["AI Assistant"])

@router.post("/chat", response_model=ChatResponse)
async def chat(
    req: ChatRequest,
    raw_request: Request,
    authorization: str = Header(..., description="Bearer JWT token from Go core banking API")
):
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid authorization header format. Expected Bearer <token>")
    
    token = authorization.split(" ")[1]

    response = await agent_service.process_chat(
        messages=req.messages,
        auth_token=token,
        api_key_override=req.openrouter_api_key,
        model_override=req.model
    )
    return response
