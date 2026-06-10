from fastapi import APIRouter, HTTPException
import logging

from app.schemas.llm import GenerateRequest, GenerateResponse, SessionSummaryResponse
from app.core.router import llm_router, get_session_summary
from app.core.cache import get_cached_completion, set_cached_completion
from app.core.compression import compress_prompt

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
        # 1. Optimize prompt layout and trim HTML contexts
        request.prompt = compress_prompt(request.prompt)
        
        # 2. Query caching layer to achieve 100% token savings on identical repeat scans
        cached_res = get_cached_completion(request.prompt, request.system_message)
        if cached_res:
            if request.session_id:
                try:
                    from app.core.router import track_session_tokens
                    # Track cached tokens with 0.0 cost (100% cost savings!)
                    track_session_tokens(
                        session_id=request.session_id,
                        provider=cached_res.get("provider", "mock"),
                        input_tokens=cached_res.get("input_tokens", 0),
                        output_tokens=cached_res.get("output_tokens", 0),
                        cost=0.0,
                        agent_type=request.agent_type
                    )
                except Exception as track_err:
                    logger.error(f"Error tracking cached completion tokens: {str(track_err)}")
            return GenerateResponse(**cached_res)
            
        # 3. Process LLM call (standard fallback list)
        response = await llm_router.execute_generate(request)
        
        # 4. Cache newly completed response for subsequent scans
        cache_data = response.model_dump()
        cache_data["cached"] = True
        set_cached_completion(request.prompt, request.system_message, cache_data)
        
        return response
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
        return get_session_summary(session_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch session totals: {str(e)}")

@router.get("/health")
async def health_check():
    """
    Standard microservice health status check.
    """
    return {"status": "ok", "service": "llm-central-service"}
