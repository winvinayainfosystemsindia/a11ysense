import logging
from app.schemas.llm import GenerateRequest, GenerateResponse, SessionSummaryResponse
from app.core.compression import compress_prompt
from app.core.router import llm_router
from app.repository.cache_repo import cache_repo
from app.repository.session_repo import session_repo

logger = logging.getLogger(__name__)

class LLMService:
    async def generate_completion(self, request: GenerateRequest) -> GenerateResponse:
        """
        Centralized generation handler. Resolves completions with prompt layout compression,
        caching lookups, model-fallback client chains, and session pricing/token tracking.
        """
        # 1. Optimize prompt layout and trim HTML contexts
        request.prompt = compress_prompt(request.prompt)
        
        # 2. Query caching layer to achieve 100% token savings on identical repeat scans
        cached_res = cache_repo.get_cached_completion(request.prompt, request.system_message)
        if cached_res:
            if request.session_id:
                try:
                    # Track cached tokens with 0.0 cost (100% cost savings!)
                    session_repo.track_session_tokens(
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
        cache_repo.set_cached_completion(request.prompt, request.system_message, cache_data)
        
        return response

    def get_session_summary(self, session_id: str) -> SessionSummaryResponse:
        """
        Fetches cumulative token usage metrics and costs for the requested session ID.
        """
        return session_repo.get_session_summary(session_id)

llm_service = LLMService()
