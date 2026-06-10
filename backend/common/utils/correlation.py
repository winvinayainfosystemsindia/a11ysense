import contextvars
import uuid
from typing import Dict

# Async-safe request correlation storage context
CORRELATION_ID_VAR = contextvars.ContextVar("correlation_id", default=None)

def get_correlation_id() -> str:
    """
    Retrieves the current execution context's request correlation ID.
    If none is set, generates a new fallback UUID and binds it.
    """
    cid = CORRELATION_ID_VAR.get()
    if cid is None:
        cid = str(uuid.uuid4())
        CORRELATION_ID_VAR.set(cid)
    return cid

def set_correlation_id(correlation_id: str) -> None:
    """
    Binds a specific correlation ID to the current async context.
    """
    CORRELATION_ID_VAR.set(correlation_id)

def get_correlation_headers() -> Dict[str, str]:
    """
    Returns standard headers containing the current request context's correlation ID
    for downstream service calls.
    """
    return {"X-Correlation-ID": get_correlation_id()}
