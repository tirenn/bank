import json
import logging
from typing import List, Dict, Any, Optional
import redis.asyncio as aioredis
from app.config import settings
from app.domain.schemas import ChatMessage

logger = logging.getLogger("ai_service.services.chat_history")

class ConversationHistoryService:
    """
    Redis List-backed Conversation History Service:
    - Stores messages per user in Redis list: 'chat:history:{user_id}'
    - Retrieves last 10 turns (or specified count) for context awareness
    - 1 Day (86,400s) TTL refreshed on every message
    - Clear/delete session endpoint for resetting conversation context
    """

    def __init__(self, redis_url: str = settings.REDIS_URL, ttl_seconds: int = 86400):
        self.redis_url = redis_url
        self.ttl_seconds = ttl_seconds  # 1 day = 86400 seconds
        self.redis: Optional[aioredis.Redis] = None

    async def connect(self):
        if self.redis is None:
            try:
                self.redis = aioredis.from_url(self.redis_url, decode_responses=True)
                await self.redis.ping()
                logger.info(f"Connected to Redis for Conversation History at {self.redis_url}")
            except Exception as e:
                logger.warning(f"Redis unavailable for conversation history: {e}")
                self.redis = None

    def _get_key(self, session_or_user_id: str) -> str:
        return f"chat:history:{session_or_user_id}"

    async def get_history(self, session_or_user_id: str, limit: int = 10) -> List[ChatMessage]:
        """
        Retrieves the last `limit` conversation messages from the Redis list.
        """
        if not self.redis:
            await self.connect()
        if not self.redis:
            return []

        key = self._get_key(session_or_user_id)
        try:
            # Get the last `limit` items from the Redis list
            raw_messages = await self.redis.lrange(key, -limit, -1)
            messages: List[ChatMessage] = []
            for item_str in raw_messages:
                try:
                    data = json.loads(item_str)
                    messages.append(ChatMessage(
                        role=data.get("role", "user"),
                        content=data.get("content", "")
                    ))
                except Exception as parse_err:
                    logger.warning(f"Error parsing conversation message from Redis: {parse_err}")
            return messages
        except Exception as e:
            logger.error(f"Error reading conversation history from Redis: {e}")
            return []

    async def append_turn(
        self,
        session_or_user_id: str,
        user_message: str,
        assistant_reply: str,
        action_type: Optional[str] = None,
        action_data: Optional[Dict[str, Any]] = None,
        tools_used: Optional[List[str]] = None
    ):
        """
        Appends a user message and assistant reply to the Redis list and sets 1-day TTL.
        """
        if not self.redis:
            await self.connect()
        if not self.redis:
            return

        key = self._get_key(session_or_user_id)
        try:
            pipe = self.redis.pipeline()
            # Push user message
            user_payload = json.dumps({
                "role": "user",
                "content": user_message
            })
            pipe.rpush(key, user_payload)

            # Push assistant reply
            assistant_payload = json.dumps({
                "role": "assistant",
                "content": assistant_reply,
                "action_type": action_type,
                "action_data": action_data,
                "tools_used": tools_used or []
            })
            pipe.rpush(key, assistant_payload)

            # Refresh 1-day (86,400s) TTL
            pipe.expire(key, self.ttl_seconds)
            await pipe.execute()
            logger.info(f"Saved conversation turn to Redis for user '{session_or_user_id}' with TTL={self.ttl_seconds}s")
        except Exception as e:
            logger.error(f"Error appending conversation turn to Redis: {e}")

    async def clear_history(self, session_or_user_id: str) -> bool:
        """
        Deletes the conversation session from Redis.
        """
        if not self.redis:
            await self.connect()
        if not self.redis:
            return False

        key = self._get_key(session_or_user_id)
        try:
            await self.redis.delete(key)
            logger.info(f"Deleted conversation history for session/user '{session_or_user_id}' from Redis.")
            return True
        except Exception as e:
            logger.error(f"Error deleting conversation history from Redis: {e}")
            return False

chat_history_service = ConversationHistoryService()
