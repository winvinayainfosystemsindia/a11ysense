from fastapi import APIRouter, HTTPException
import logging

from app.schemas.llm import GenerateRequest, GenerateResponse, SessionSummaryResponse
from app.services.llm_service import llm_service

logger = logging.getLogger(__name__)
router = APIRouter()

@router.post("/generate", response_model=GenerateResponse)
async def generate_completion(request: GenerateRequest):
    """
    Centralized generation endpoint. Resolves completions with:
    1. Indentation & HTML node compression (token savings).
    2. Caching lookup (instant response on identical scans).
    3. Statefull Model Fallback client chains.
    4. Session pricing estimations.
    """
    try:
        return await llm_service.generate_completion(request)
    except Exception as e:
        logger.exception("Error executing centralization LLM request")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/session/{session_id}", response_model=SessionSummaryResponse)
async def fetch_session_summary(session_id: str):
    """
    Fetches the cumulative token usage, costs, and model distributions 
    accumulated under the requested session ID.
    """
    try:
        return llm_service.get_session_summary(session_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch session totals: {str(e)}")

@router.get("/health")
async def health_check():
    """
    Standard microservice health status check.
    """
    return {"status": "ok", "service": "llm-central-service"}
