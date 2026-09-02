import time
import logging
from typing import Optional
import redis.asyncio as aioredis
from fastapi import HTTPException, Request

logger = logging.getLogger("ai_service.rate_limiter")

class RedisSlidingWindowRateLimiter:
    def __init__(self, redis_url: str, max_requests: int = 60, window_sec: int = 60):
        self.redis_url = redis_url
        self.max_requests = max_requests
        self.window_sec = window_sec
        self.redis: Optional[aioredis.Redis] = None

    async def connect(self):
        try:
            self.redis = aioredis.from_url(self.redis_url, decode_responses=True)
            await self.redis.ping()
            logger.info("Connected to Redis for sliding window rate limiter")
        except Exception as e:
            logger.warning(f"Redis unavailable, rate limiter running in bypass mode: {e}")
            self.redis = None

    async def check(self, request: Request, identifier: Optional[str] = None):
        if not self.redis:
            return

        client_ip = identifier or request.client.host or "127.0.0.1"
        key = f"rate_limit:ai:{client_ip}"
        now = time.time()
        clear_before = now - self.window_sec

        try:
            pipe = self.redis.pipeline()
            pipe.zremrangebyscore(key, 0, clear_before)
            pipe.zadd(key, {str(now): now})
            pipe.zcard(key)
            pipe.expire(key, self.window_sec + 10)
            results = await pipe.execute()

            current_requests = results[2]
            if current_requests > self.max_requests:
                logger.warn(f"Rate limit exceeded for client {client_ip} ({current_requests}/{self.max_requests})")
                raise HTTPException(
                    status_code=429,
                    detail=f"Too Many Requests. Rate limit of {self.max_requests} req/min exceeded. Please try again in a moment."
                )
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error executing Redis rate limiter: {e}")
