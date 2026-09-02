from fastapi import APIRouter
from app.api.v1.chat import router as chat_router
from app.api.v1.faq import router as faq_router

api_v1_router = APIRouter(prefix="/api/v1")
api_v1_router.include_router(chat_router)
api_v1_router.include_router(faq_router)

__all__ = ["api_v1_router"]
