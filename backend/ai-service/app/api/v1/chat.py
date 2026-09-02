from fastapi import APIRouter, Header, HTTPException, Request
from app.domain.schemas import ChatRequest, ChatResponse
from app.services.agent_service import agent_service
from app.services.model_fallback import fetch_models_from_db
from app.services.chat_history_service import chat_history_service
from app.api.dependencies import extract_user_from_token

router = APIRouter(prefix="/ai", tags=["AI Assistant"])


@router.get("/models")
async def get_models():
    """
    Returns the list of active AI models directly from the PostgreSQL database via Core Banking API.
    """
    models = await fetch_models_from_db()
    return {
        "models": models,
        "default_model": models[0] if models else "google/gemini-2.0-flash-exp:free"
    }


@router.post("/chat", response_model=ChatResponse)
async def chat(
    req: ChatRequest,
    raw_request: Request,
    authorization: str = Header(..., description="Bearer JWT token from Go core banking API")
):
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid authorization header format. Expected Bearer <token>")
    
    token = authorization.split(" ")[1]
    user_payload = extract_user_from_token(token)
    user_id = str(user_payload.get("user_id", user_payload.get("email", "default_user")))

    # 1. Validate selected model from user against active database models
    if req.model and req.model.strip():
        selected_model = req.model.strip()
        active_models = await fetch_models_from_db()
        if active_models and selected_model not in active_models:
            raise HTTPException(
                status_code=400,
                detail=f"Selected AI model '{selected_model}' is not registered or active in the database. Please select a valid model."
            )

    # 2. Retrieve previous 10 conversation messages from Redis List for full contextual awareness
    history_messages = await chat_history_service.get_history(user_id, limit=10)
    
    if history_messages and req.messages:
        # Prepend the previous 10 conversation turns before the latest message
        latest_user_message = req.messages[-1]
        context_messages = history_messages + [latest_user_message]
    else:
        context_messages = req.messages

    # 3. Execute multi-agent processing with context
    response = await agent_service.process_chat(
        messages=context_messages,
        auth_token=token,
        api_key_override=req.openrouter_api_key,
        model_override=req.model.strip() if req.model else None
    )

    # 4. Save conversation turn to Redis List with 1-day TTL (86,400 seconds)
    if req.messages and response and response.reply:
        last_user_text = req.messages[-1].content
        await chat_history_service.append_turn(
            session_or_user_id=user_id,
            user_message=last_user_text,
            assistant_reply=response.reply,
            action_type=response.action_type,
            action_data=response.action_data,
            tools_used=response.tools_used
        )

    return response


@router.delete("/session")
@router.post("/session/reset")
async def reset_chat_session(
    authorization: str = Header(..., description="Bearer JWT token from Go core banking API")
):
    """
    Deletes all conversation history stored in Redis list for the authenticated user session.
    """
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid authorization header format. Expected Bearer <token>")
    
    token = authorization.split(" ")[1]
    user_payload = extract_user_from_token(token)
    user_id = str(user_payload.get("user_id", user_payload.get("email", "default_user")))

    success = await chat_history_service.clear_history(user_id)
    return {
        "status": "success",
        "message": f"Conversation session for user '{user_id}' cleared successfully from Redis.",
        "cleared": success
    }


@router.get("/session/history")
async def get_session_history(
    authorization: str = Header(..., description="Bearer JWT token from Go core banking API")
):
    """
    Retrieves the active conversation history from Redis list for the authenticated user session.
    """
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid authorization header format. Expected Bearer <token>")
    
    token = authorization.split(" ")[1]
    user_payload = extract_user_from_token(token)
    user_id = str(user_payload.get("user_id", user_payload.get("email", "default_user")))

    history = await chat_history_service.get_history(user_id, limit=20)
    return {
        "user_id": user_id,
        "total_messages": len(history),
        "history": history
    }



