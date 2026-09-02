import json
import logging
from datetime import datetime, timezone
from typing import Optional, Dict, Any, List
import redis.asyncio as redis
from app.config import settings
from app.domain.schemas import WorkflowState
from app.logger import app_logger as logger

class WorkflowStateService:
    """
    Manages Long-Running Multi-Turn Workflow State in Redis with isolated 7-day TTL keys.
    Key Pattern: workflow:{workflow_type}:{user_id} and index workflow:active:{user_id}
    """

    def __init__(self):
        self.rdb: Optional[redis.Redis] = None
        self._default_ttl_seconds = 604800  # 7 Days (7 * 24 * 3600)

    async def connect(self):
        try:
            self.rdb = redis.from_url(
                settings.REDIS_URL,
                decode_responses=True,
                socket_timeout=3.0,
                socket_connect_timeout=3.0
            )
            await self.rdb.ping()
            logger.info("Connected to Redis for Long-Running Multi-Turn Workflow Engine (7-Day TTL)")
        except Exception as e:
            logger.warning(f"Failed to connect Redis for Workflow Engine ({e}). Fallback to in-memory/disabled mode.")
            self.rdb = None

    def _get_workflow_key(self, user_id: str, workflow_type: str) -> str:
        return f"workflow:{workflow_type.lower().strip()}:{user_id.strip()}"

    def _get_active_index_key(self, user_id: str) -> str:
        return f"workflow:active:{user_id.strip()}"

    async def get_active_workflow(self, user_id: str, workflow_type: Optional[str] = None) -> Optional[WorkflowState]:
        """
        Retrieves active long-running workflow state for a user.
        """
        if not self.rdb:
            return None

        try:
            if workflow_type:
                target_key = self._get_workflow_key(user_id, workflow_type)
            else:
                # Check active pointer key
                active_type = await self.rdb.get(self._get_active_index_key(user_id))
                if not active_type:
                    return None
                target_key = self._get_workflow_key(user_id, active_type)

            data_str = await self.rdb.get(target_key)
            if not data_str:
                return None

            parsed = json.loads(data_str)
            return WorkflowState(**parsed)
        except Exception as e:
            logger.error(f"[Workflow Engine] Failed to get workflow for user '{user_id}': {e}")
            return None

    async def save_workflow(self, workflow: WorkflowState, ttl_seconds: Optional[int] = None) -> bool:
        """
        Saves or updates a workflow state in Redis with 7-day TTL.
        """
        if not self.rdb:
            return False

        ttl = ttl_seconds or self._default_ttl_seconds
        target_key = self._get_workflow_key(workflow.user_id, workflow.workflow_type)
        active_index_key = self._get_active_index_key(workflow.user_id)

        try:
            workflow.updated_at = datetime.now(timezone.utc).isoformat()
            payload = workflow.model_dump_json()

            async with self.rdb.pipeline() as pipe:
                pipe.set(target_key, payload, ex=ttl)
                if workflow.status in ("IN_PROGRESS", "WAITING_FOR_USER_INPUT"):
                    pipe.set(active_index_key, workflow.workflow_type.lower().strip(), ex=ttl)
                else:
                    pipe.delete(active_index_key)
                await pipe.execute()

            logger.info(
                f"💾 [Workflow State Saved] User: {workflow.user_id} | Type: {workflow.workflow_type} | "
                f"Step: {workflow.current_step}/{workflow.total_steps} (TTL: {ttl}s)"
            )
            return True
        except Exception as e:
            logger.error(f"[Workflow Engine] Failed to save workflow: {e}")
            return False

    async def advance_workflow(
        self,
        user_id: str,
        workflow_type: str,
        step: int,
        new_data: Dict[str, Any],
        next_status: str = "IN_PROGRESS"
    ) -> Optional[WorkflowState]:
        """
        Advances the workflow step and merges newly collected form fields.
        """
        active = await self.get_active_workflow(user_id, workflow_type)
        now_iso = datetime.now(timezone.utc).isoformat()

        if not active:
            active = WorkflowState(
                workflow_id=f"wf_{workflow_type.lower()}_{int(datetime.now().timestamp())}",
                workflow_type=workflow_type.upper(),
                user_id=user_id,
                current_step=step,
                total_steps=4,
                status=next_status,
                collected_data=new_data,
                created_at=now_iso,
                updated_at=now_iso
            )
        else:
            active.current_step = step
            active.status = next_status
            active.collected_data.update(new_data)
            active.updated_at = now_iso

        success = await self.save_workflow(active)
        return active if success else None

    async def complete_workflow(self, user_id: str, workflow_type: str) -> bool:
        """
        Marks workflow as SUBMITTED and removes active pointer from Redis.
        """
        if not self.rdb:
            return False

        target_key = self._get_workflow_key(user_id, workflow_type)
        active_index_key = self._get_active_index_key(user_id)

        try:
            async with self.rdb.pipeline() as pipe:
                pipe.delete(target_key)
                pipe.delete(active_index_key)
                await pipe.execute()
            logger.info(f"✅ [Workflow Completed] User: {user_id} | Type: {workflow_type} removed from draft queue.")
            return True
        except Exception as e:
            logger.error(f"[Workflow Engine] Failed to complete workflow: {e}")
            return False

    async def cancel_workflow(self, user_id: str, workflow_type: Optional[str] = None) -> bool:
        """
        Cancels active workflow and purges Redis keys.
        """
        if not self.rdb:
            return False

        try:
            active_type = workflow_type
            if not active_type:
                active_type = await self.rdb.get(self._get_active_index_key(user_id))

            if active_type:
                target_key = self._get_workflow_key(user_id, active_type)
                active_index_key = self._get_active_index_key(user_id)
                async with self.rdb.pipeline() as pipe:
                    pipe.delete(target_key)
                    pipe.delete(active_index_key)
                    await pipe.execute()
                logger.info(f"🚫 [Workflow Cancelled] User: {user_id} | Type: {active_type} purged.")
                return True
            return False
        except Exception as e:
            logger.error(f"[Workflow Engine] Failed to cancel workflow: {e}")
            return False


workflow_state_service = WorkflowStateService()
