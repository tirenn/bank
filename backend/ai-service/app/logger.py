import json
import logging
import sys
from datetime import datetime, timezone
from contextvars import ContextVar
from typing import Any, Dict, Optional

request_id_ctx: ContextVar[Optional[str]] = ContextVar("request_id", default=None)
trace_id_ctx: ContextVar[Optional[str]] = ContextVar("trace_id", default=None)

from app.services.pii_redactor import redact_text, redact_data

class StructuredJsonFormatter(logging.Formatter):
    def __init__(self, service_name: str = "bank-ai", environment: str = "development"):
        super().__init__()
        self.service_name = service_name
        self.environment = environment

    def format(self, record: logging.LogRecord) -> str:
        log_obj: Dict[str, Any] = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "service": self.service_name,
            "environment": self.environment,
            "caller": f"{record.filename}:{record.lineno}",
            "message": redact_text(record.getMessage(), mask_email=True),
        }

        req_id = request_id_ctx.get()
        if req_id:
            log_obj["request_id"] = req_id

        trace_id = trace_id_ctx.get()
        if trace_id:
            log_obj["trace_id"] = trace_id

        if hasattr(record, "fields") and isinstance(record.fields, dict):
            log_obj["fields"] = redact_data(record.fields, mask_email=True)

        if record.exc_info:
            log_obj["error"] = redact_text(self.formatException(record.exc_info), mask_email=True)

        return json.dumps(log_obj)


def create_app_logger(service_name: str = "bank-ai", environment: str = "development") -> logging.Logger:
    logger = logging.getLogger("bank_ai")
    logger.setLevel(logging.INFO)
    logger.handlers.clear()

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(StructuredJsonFormatter(service_name=service_name, environment=environment))
    handler.setLevel(logging.INFO)

    logger.addHandler(handler)
    logger.propagate = False
    return logger

app_logger = create_app_logger()

def setup_logger(service_name: str = "bank-ai", environment: str = "development") -> logging.Logger:
    return create_app_logger(service_name, environment)
