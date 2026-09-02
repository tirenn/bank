import hashlib
import json
import logging
import re
import time
from typing import Optional, Dict, Any, List
import numpy as np
import redis.asyncio as aioredis
from chromadb.utils import embedding_functions
from app.config import settings

logger = logging.getLogger("ai_service.services.rag_cache")

class RedisSemanticRagCache:
    """
    Redis-Native Semantic RAG Answer Cache:
    1. Exact / Normalized Query Matching via Redis STRING keys (0-2 ms).
    2. Semantic Vector Similarity Matching directly in Redis HASH & SET structures (2-5 ms).
    """

    def __init__(
        self,
        redis_url: str = settings.REDIS_URL,
        ttl: int = settings.RAG_CACHE_TTL,
        similarity_threshold: float = 0.58
    ):
        self.redis_url = redis_url
        self.ttl = ttl
        self.similarity_threshold = similarity_threshold  # Cosine similarity >= 0.58 for semantic match
        self.redis: Optional[aioredis.Redis] = None
        self._emb_fn = None

    @property
    def emb_fn(self):
        if self._emb_fn is None:
            self._emb_fn = embedding_functions.DefaultEmbeddingFunction()
        return self._emb_fn

    async def connect(self):
        if self.redis is None:
            try:
                self.redis = aioredis.from_url(self.redis_url, decode_responses=True)
                await self.redis.ping()
                logger.info(f"Connected to Redis for Semantic RAG Caching at {self.redis_url}")
            except Exception as e:
                logger.warning(f"Redis unavailable for semantic cache (running in bypass mode): {e}")
                self.redis = None

    @staticmethod
    def normalize_query(query: str) -> str:
        if not query:
            return ""
        text = query.lower().strip()
        text = re.sub(r"[^\w\s]", "", text)
        text = " ".join(text.split())
        return text

    def _get_exact_key(self, normalized_query: str) -> str:
        query_hash = hashlib.sha256(normalized_query.encode("utf-8")).hexdigest()
        return f"rag:cache:exact:{query_hash}"

    def _get_semantic_key(self, entry_id: str) -> str:
        return f"rag:semantic:entry:{entry_id}"

    async def get_cached_answer(self, query: str) -> Optional[Dict[str, Any]]:
        """
        Retrieves cached RAG answer from Redis:
        1. Exact string match in Redis.
        2. Semantic similarity vector search across all Redis semantic entries.
        """
        if not self.redis:
            await self.connect()
        if not self.redis:
            return None

        normalized = self.normalize_query(query)
        if not normalized:
            return None

        # --- Tier 1: Exact Match in Redis (1 ms) ---
        exact_key = self._get_exact_key(normalized)
        try:
            raw_exact = await self.redis.get(exact_key)
            if raw_exact:
                parsed = json.loads(raw_exact)
                logger.info(f"⚡ [Redis Exact Match HIT] query: '{query}' -> key={exact_key}")
                return parsed
        except Exception as e:
            logger.error(f"Error reading exact cache from Redis: {e}")

        # --- Tier 2: Semantic Vector Similarity Search in Redis ---
        try:
            active_ids = await self.redis.smembers("rag:semantic:index")
            if not active_ids:
                logger.info(f"🔍 [Redis Semantic Cache Empty] query: '{query}'")
                return None

            # Compute query vector
            query_vector = self.emb_fn([normalized])[0]
            query_norm = np.linalg.norm(query_vector)
            if query_norm == 0:
                return None

            # Batch retrieve semantic entries from Redis using pipeline
            pipe = self.redis.pipeline()
            id_list = list(active_ids)
            for eid in id_list:
                pipe.hgetall(self._get_semantic_key(eid))
            entries = await pipe.execute()

            best_match = None
            best_sim = -1.0
            expired_ids = []

            for eid, entry in zip(id_list, entries):
                if not entry or "embedding" not in entry:
                    expired_ids.append(eid)
                    continue

                try:
                    entry_emb = np.array(json.loads(entry["embedding"]), dtype=np.float32)
                    entry_norm = np.linalg.norm(entry_emb)
                    if entry_norm == 0:
                        continue

                    sim = float(np.dot(query_vector, entry_emb) / (query_norm * entry_norm))
                    if sim > best_sim:
                        best_sim = sim
                        best_match = entry
                except Exception as parse_err:
                    logger.warning(f"Error parsing Redis semantic entry {eid}: {parse_err}")

            # Clean up expired index references in Redis in background
            if expired_ids:
                try:
                    await self.redis.srem("rag:semantic:index", *expired_ids)
                except Exception:
                    pass

            # Check if best match passes the semantic similarity threshold
            if best_match and best_sim >= self.similarity_threshold:
                logger.info(
                    f"🧠 [Redis Semantic HIT] query: '{query}' matched Redis entry '{best_match.get('original_query')}' "
                    f"(similarity={best_sim:.4f} >= threshold={self.similarity_threshold})"
                )

                action_type_val = best_match.get("action_type")
                action_data_str = best_match.get("action_data_json", "null")

                result = {
                    "query": query,
                    "matched_query": best_match.get("original_query"),
                    "similarity_score": round(best_sim, 4),
                    "reply": best_match.get("reply", ""),
                    "action_type": action_type_val if action_type_val and action_type_val != "None" else None,
                    "action_data": json.loads(action_data_str) if action_data_str and action_data_str != "null" else None,
                    "tools_used": ["search_bank_faq (redis_semantic_cached)"],
                    "source": "redis_semantic_cache"
                }

                # Auto-populate exact Redis key for this new variation
                if result["reply"]:
                    try:
                        await self.redis.set(exact_key, json.dumps(result), ex=self.ttl)
                    except Exception:
                        pass

                return result
            else:
                logger.info(
                    f"🔍 [Redis Semantic MISS] Best similarity={best_sim:.4f} < threshold={self.similarity_threshold} for query: '{query}'"
                )

        except Exception as e:
            logger.error(f"Error executing Redis semantic cache lookup: {e}")

        return None

    async def set_cached_answer(
        self,
        query: str,
        reply: str,
        action_type: Optional[str] = None,
        action_data: Optional[Dict[str, Any]] = None,
        tools_used: Optional[list] = None,
        ttl: Optional[int] = None
    ) -> bool:
        """
        Stores RAG answer directly into Redis:
        1. Redis Exact Key (`rag:cache:exact:{hash}`)
        2. Redis Semantic Hash (`rag:semantic:entry:{hash}`) with Vector Embedding
        3. Redis Semantic Set Index (`rag:semantic:index`)
        """
        if not self.redis:
            await self.connect()
        if not self.redis:
            return False

        normalized = self.normalize_query(query)
        if not normalized or not reply or not reply.strip():
            return False

        expiry = ttl or self.ttl
        query_hash = hashlib.sha256(normalized.encode("utf-8")).hexdigest()
        entry_id = f"sem_{query_hash}"

        exact_key = self._get_exact_key(normalized)
        semantic_key = self._get_semantic_key(entry_id)

        try:
            # 1. Compute embedding vector
            emb = self.emb_fn([normalized])[0]
            emb_list = [float(x) for x in emb]

            # 2. Save Exact Key
            exact_payload = {
                "query": query,
                "normalized_query": normalized,
                "reply": reply,
                "action_type": action_type,
                "action_data": action_data,
                "tools_used": tools_used or ["search_bank_faq (cached)"],
                "cached_at": time.time(),
                "source": "redis_exact_cache"
            }
            await self.redis.set(exact_key, json.dumps(exact_payload), ex=expiry)

            # 3. Save Semantic Entry Hash in Redis
            pipe = self.redis.pipeline()
            pipe.hset(semantic_key, mapping={
                "entry_id": entry_id,
                "original_query": query,
                "normalized_query": normalized,
                "embedding": json.dumps(emb_list),
                "reply": reply,
                "action_type": str(action_type) if action_type else "None",
                "action_data_json": json.dumps(action_data) if action_data else "null",
                "tools_used_json": json.dumps(tools_used or ["search_bank_faq"]),
                "cached_at": str(time.time())
            })
            pipe.expire(semantic_key, expiry)
            pipe.sadd("rag:semantic:index", entry_id)
            await pipe.execute()

            logger.info(f"💾 [Redis Semantic SAVED] query: '{query}' -> entry={entry_id} in Redis (TTL={expiry}s)")
            return True
        except Exception as e:
            logger.error(f"Error saving to Redis semantic cache: {e}")
            return False

    async def invalidate_all(self) -> int:
        """
        Invalidates all semantic and exact RAG caches stored in Redis.
        """
        if not self.redis:
            await self.connect()
        if not self.redis:
            return 0

        deleted_count = 0
        try:
            # 1. Get all semantic entries from Redis Set
            entry_ids = await self.redis.smembers("rag:semantic:index")
            if entry_ids:
                semantic_keys = [self._get_semantic_key(eid) for eid in entry_ids]
                deleted_count += await self.redis.delete(*semantic_keys)
                await self.redis.delete("rag:semantic:index")

            # 2. Purge all exact cache keys from Redis
            cursor = 0
            while True:
                cursor, keys = await self.redis.scan(cursor=cursor, match="rag:cache:*", count=100)
                if keys:
                    deleted_count += await self.redis.delete(*keys)
                if cursor == 0:
                    break

            cursor2 = 0
            while True:
                cursor2, keys2 = await self.redis.scan(cursor2=cursor2, match="rag:semantic:*", count=100)
                if keys2:
                    deleted_count += await self.redis.delete(*keys2)
                if cursor2 == 0:
                    break

            logger.info(f"🧹 [Redis Semantic Invalidation] Cleared {deleted_count} cache keys from Redis.")
            return deleted_count
        except Exception as e:
            logger.error(f"Error invalidating Redis semantic cache: {e}")
            return 0

rag_cache_service = RedisSemanticRagCache()