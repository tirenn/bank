import json
import logging
from datetime import datetime, timezone
from typing import Optional, Dict, Any, List, Tuple

import httpx
import redis.asyncio as redis
from app.config import settings
from app.logger import app_logger as logger

class CostTrackerService:
    """
    Real-time AI Token & Cost Tracking Service.
    Calculates cost dynamically based on OpenRouter Pricing API and aggregates telemetry in Redis.
    """

    def __init__(self):
        self.rdb: Optional[redis.Redis] = None
        self._pricing_cache_ttl = 86400  # 24 Hours
        self._mem_pricing: Dict[str, Dict[str, float]] = {}

    async def connect(self):
        try:
            self.rdb = redis.from_url(
                settings.REDIS_URL,
                decode_responses=True,
                socket_timeout=3.0,
                socket_connect_timeout=3.0
            )
            await self.rdb.ping()
            logger.info("Connected to Redis for AI Token & Cost Tracking Service")
        except Exception as e:
            logger.warning(f"Failed to connect Redis for Cost Tracker ({e}). Running in in-memory fallback mode.")
            self.rdb = None

    async def fetch_and_cache_pricing(self) -> Dict[str, Dict[str, float]]:
        """
        Fetches the OpenRouter model pricing catalog and caches rates per token in Redis & memory.
        """
        # 1. Check Redis cache first
        if self.rdb:
            try:
                cached_json = await self.rdb.get("openrouter:pricing:catalog")
                if cached_json:
                    self._mem_pricing = json.loads(cached_json)
                    return self._mem_pricing
            except Exception as e:
                logger.debug(f"[Cost Tracker] Redis pricing cache read note: {e}")

        # 2. Fetch from OpenRouter public models endpoint
        pricing_map: Dict[str, Dict[str, float]] = {}
        try:
            async with httpx.AsyncClient(timeout=8.0) as client:
                res = await client.get("https://openrouter.ai/api/v1/models")
                if res.status_code == 200:
                    models_data = res.json().get("data", [])
                    for m in models_data:
                        model_id = m.get("id")
                        pricing = m.get("pricing", {})
                        if model_id and pricing:
                            try:
                                prompt_rate = float(pricing.get("prompt", 0.0))
                                completion_rate = float(pricing.get("completion", 0.0))
                                pricing_map[model_id] = {
                                    "prompt": prompt_rate,
                                    "completion": completion_rate
                                }
                            except (ValueError, TypeError):
                                pass

                    if pricing_map:
                        self._mem_pricing = pricing_map
                        if self.rdb:
                            try:
                                await self.rdb.set("openrouter:pricing:catalog", json.dumps(pricing_map), ex=self._pricing_cache_ttl)
                            except Exception:
                                pass
                        logger.info(f"Loaded and cached {len(pricing_map)} OpenRouter model pricing rates")
                        return pricing_map
        except Exception as e:
            logger.warning(f"[Cost Tracker] Failed to fetch live OpenRouter pricing catalog ({e}), using default base rates.")

        return self._mem_pricing

    def _get_rates_for_model(self, model_slug: str) -> Tuple[float, float]:
        """
        Returns (rate_per_prompt_token, rate_per_completion_token) in USD.
        """

        slug = model_slug.strip().lower() if model_slug else ""
        # Free models always cost $0.00
        if ":free" in slug or "openrouter/free" in slug:
            return 0.0, 0.0

        if model_slug in self._mem_pricing:
            p = self._mem_pricing[model_slug]
            return p.get("prompt", 0.0), p.get("completion", 0.0)

        # Baseline fallback pricing if model not in cached catalog
        if "gpt-4" in slug or "claude-3" in slug:
            return 0.000003, 0.000015  # ~$3/1M prompt, $15/1M completion
        elif "mini" in slug or "flash" in slug or "haiku" in slug:
            return 0.00000015, 0.0000006  # ~$0.15/1M prompt, $0.60/1M completion
        
        return 0.000001, 0.000002

    async def record_usage(
        self,
        model: str,
        domain: str,
        prompt_tokens: int,
        completion_tokens: int,
        user_id: Optional[str] = "system"
    ) -> float:
        """
        Calculates and records LLM token usage and estimated cost in USD.
        """
        if prompt_tokens <= 0 and completion_tokens <= 0:
            return 0.0

        rate_in, rate_out = self._get_rates_for_model(model)
        cost_usd = (prompt_tokens * rate_in) + (completion_tokens * rate_out)
        total_tokens = prompt_tokens + completion_tokens

        logger.info(
            f"💰 [Token & Cost Telemetry] Model: {model} | Domain: {domain} | "
            f"Tokens: {total_tokens} (In: {prompt_tokens}, Out: {completion_tokens}) | Cost: ${cost_usd:.6f} USD"
        )

        if not self.rdb:
            return cost_usd

        try:
            audit_entry = {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "model": model,
                "domain": domain.upper() if domain else "GENERAL",
                "prompt_tokens": prompt_tokens,
                "completion_tokens": completion_tokens,
                "total_tokens": total_tokens,
                "cost_usd": round(cost_usd, 6),
                "user_id": str(user_id) if user_id else "anonymous"
            }

            async with self.rdb.pipeline() as pipe:
                # 1. Increment overall summary KPIs
                pipe.hincrbyfloat("cost:summary", "total_usd", cost_usd)
                pipe.hincrby("cost:summary", "total_tokens", total_tokens)
                pipe.hincrby("cost:summary", "prompt_tokens", prompt_tokens)
                pipe.hincrby("cost:summary", "completion_tokens", completion_tokens)
                pipe.hincrby("cost:summary", "total_requests", 1)

                # 2. Increment per-domain metrics
                dom_key = domain.upper() if domain else "GENERAL"
                pipe.hincrbyfloat("cost:by_domain:usd", dom_key, cost_usd)
                pipe.hincrby("cost:by_domain:tokens", dom_key, total_tokens)

                # 3. Increment per-model metrics
                mod_key = model if model else "default"
                pipe.hincrbyfloat("cost:by_model:usd", mod_key, cost_usd)
                pipe.hincrby("cost:by_model:tokens", mod_key, total_tokens)

                # 4. Push to audit stream (keep last 50 transactions)
                pipe.lpush("cost:stream", json.dumps(audit_entry))
                pipe.ltrim("cost:stream", 0, 49)

                await pipe.execute()
        except Exception as e:
            logger.error(f"[Cost Tracker] Failed to persist usage in Redis: {e}")

        return cost_usd

    async def get_cost_summary(self) -> Dict[str, Any]:
        """
        Retrieves comprehensive cost summary, domain distributions, and recent audit stream.
        """
        default_res = {
            "summary": {
                "total_usd": 0.0,
                "total_tokens": 0,
                "prompt_tokens": 0,
                "completion_tokens": 0,
                "total_requests": 0
            },
            "by_domain": {},
            "by_model": {},
            "recent_stream": []
        }

        if not self.rdb:
            return default_res

        try:
            async with self.rdb.pipeline() as pipe:
                pipe.hgetall("cost:summary")
                pipe.hgetall("cost:by_domain:usd")
                pipe.hgetall("cost:by_domain:tokens")
                pipe.hgetall("cost:by_model:usd")
                pipe.hgetall("cost:by_model:tokens")
                pipe.lrange("cost:stream", 0, 49)
                results = await pipe.execute()

            raw_summary = results[0] or {}
            dom_usd = results[1] or {}
            dom_tokens = results[2] or {}
            mod_usd = results[3] or {}
            mod_tokens = results[4] or {}
            raw_stream = results[5] or []

            # Format summary
            summary = {
                "total_usd": round(float(raw_summary.get("total_usd", 0.0)), 6),
                "total_tokens": int(raw_summary.get("total_tokens", 0)),
                "prompt_tokens": int(raw_summary.get("prompt_tokens", 0)),
                "completion_tokens": int(raw_summary.get("completion_tokens", 0)),
                "total_requests": int(raw_summary.get("total_requests", 0))
            }

            # Format by domain
            by_domain: Dict[str, Dict[str, Any]] = {}
            for d in ["TRANSACTION", "WEALTH", "SECURITY", "IDENTITY", "SUPPORT", "SUPERVISOR", "GENERAL"]:
                u = round(float(dom_usd.get(d, 0.0)), 6)
                t = int(dom_tokens.get(d, 0))
                if u > 0 or t > 0:
                    by_domain[d] = {"cost_usd": u, "tokens": t}

            # Format by model
            by_model: Dict[str, Dict[str, Any]] = {}
            all_model_keys = set(list(mod_usd.keys()) + list(mod_tokens.keys()))
            for m in all_model_keys:
                u = round(float(mod_usd.get(m, 0.0)), 6)
                t = int(mod_tokens.get(m, 0))
                by_model[m] = {"cost_usd": u, "tokens": t}

            # Format recent stream
            recent_stream: List[Dict[str, Any]] = []
            for item_str in raw_stream:
                try:
                    recent_stream.append(json.loads(item_str))
                except Exception:
                    pass

            return {
                "summary": summary,
                "by_domain": by_domain,
                "by_model": by_model,
                "recent_stream": recent_stream
            }
        except Exception as e:
            logger.error(f"[Cost Tracker] Failed to query summary: {e}")
            return default_res

    async def reset_metrics(self) -> bool:
        """
        Resets all cost and token tracking metrics in Redis.
        """
        if not self.rdb:
            return False

        try:
            keys_to_delete = [
                "cost:summary",
                "cost:by_domain:usd",
                "cost:by_domain:tokens",
                "cost:by_model:usd",
                "cost:by_model:tokens",
                "cost:stream"
            ]
            await self.rdb.delete(*keys_to_delete)
            logger.info("🧹 [Cost Tracker] All telemetry metrics reset successfully")
            return True
        except Exception as e:
            logger.error(f"[Cost Tracker] Failed to reset metrics: {e}")
            return False


cost_tracker_service = CostTrackerService()
