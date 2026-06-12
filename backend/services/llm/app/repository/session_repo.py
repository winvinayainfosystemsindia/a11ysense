import json
import logging
from typing import Dict, Any, Optional

from app.schemas.llm import SessionSummaryResponse
from app.repository.cache_repo import cache_repo

logger = logging.getLogger(__name__)

# In-memory fallback database for session totals (if Redis is down)
_memory_sessions: Dict[str, Dict[str, Any]] = {}

class SessionRepository:
    def track_session_tokens(
        self,
        session_id: str,
        provider: str,
        input_tokens: int,
        output_tokens: int,
        cost: float,
        agent_type: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Statefully accumulates token metrics and estimated costs per session ID using Redis,
        falling back to in-memory tracking if Redis is offline.
        """
        client = cache_repo.get_redis_client()
        key = f"llm:session:{session_id}"
        
        if client:
            try:
                data = client.get(key)
                if data:
                    session_data = json.loads(data)
                else:
                    session_data = {
                        "session_id": session_id,
                        "total_requests": 0,
                        "total_input_tokens": 0,
                        "total_output_tokens": 0,
                        "total_tokens": 0,
                        "total_cost_usd": 0.0,
                        "provider_breakdown": {},
                        "provider": provider,
                        "breakdown": {}
                    }
                    
                # Accumulate
                session_data["total_requests"] += 1
                session_data["total_input_tokens"] += input_tokens
                session_data["total_output_tokens"] += output_tokens
                session_data["total_tokens"] += (input_tokens + output_tokens)
                session_data["total_cost_usd"] = round(session_data["total_cost_usd"] + cost, 6)
                session_data["provider"] = provider
                
                pb = session_data["provider_breakdown"]
                pb[provider] = pb.get(provider, 0) + 1
                
                # Breakdown tracking
                if "breakdown" not in session_data:
                    session_data["breakdown"] = {}
                if agent_type:
                    if agent_type not in session_data["breakdown"]:
                        session_data["breakdown"][agent_type] = {
                            "provider": provider,
                            "calls": 0,
                            "tokens_sent": 0,
                            "tokens_received": 0,
                            "tokens_total": 0
                        }
                    agent_stats = session_data["breakdown"][agent_type]
                    agent_stats["provider"] = provider
                    agent_stats["calls"] += 1
                    agent_stats["tokens_sent"] += input_tokens
                    agent_stats["tokens_received"] += output_tokens
                    agent_stats["tokens_total"] += (input_tokens + output_tokens)
                
                # Save for 7 days (604800 seconds)
                client.setex(key, 604800, json.dumps(session_data))
                return session_data
            except Exception as e:
                logger.error(f"Error accumulating session tokens in Redis: {str(e)}")
                
        # In-memory fallback
        if session_id not in _memory_sessions:
            _memory_sessions[session_id] = {
                "session_id": session_id,
                "total_requests": 0,
                "total_input_tokens": 0,
                "total_output_tokens": 0,
                "total_tokens": 0,
                "total_cost_usd": 0.0,
                "provider_breakdown": {},
                "provider": provider,
                "breakdown": {}
            }
            
        s_data = _memory_sessions[session_id]
        s_data["total_requests"] += 1
        s_data["total_input_tokens"] += input_tokens
        s_data["total_output_tokens"] += output_tokens
        s_data["total_tokens"] += (input_tokens + output_tokens)
        s_data["total_cost_usd"] = round(s_data["total_cost_usd"] + cost, 6)
        s_data["provider"] = provider
        
        pb = s_data["provider_breakdown"]
        pb[provider] = pb.get(provider, 0) + 1
        
        if "breakdown" not in s_data:
            s_data["breakdown"] = {}
        if agent_type:
            if agent_type not in s_data["breakdown"]:
                s_data["breakdown"][agent_type] = {
                    "provider": provider,
                    "calls": 0,
                    "tokens_sent": 0,
                    "tokens_received": 0,
                    "tokens_total": 0
                }
            agent_stats = s_data["breakdown"][agent_type]
            agent_stats["provider"] = provider
            agent_stats["calls"] += 1
            agent_stats["tokens_sent"] += input_tokens
            agent_stats["tokens_received"] += output_tokens
            agent_stats["tokens_total"] += (input_tokens + output_tokens)
            
        return s_data

    def get_session_summary(self, session_id: str) -> SessionSummaryResponse:
        """
        Queries cumulative stats for a session ID.
        """
        client = cache_repo.get_redis_client()
        key = f"llm:session:{session_id}"
        
        if client:
            try:
                data = client.get(key)
                if data:
                    return SessionSummaryResponse(**json.loads(data))
            except Exception as e:
                logger.error(f"Error reading session details from Redis: {str(e)}")
                
        if session_id in _memory_sessions:
            return SessionSummaryResponse(**_memory_sessions[session_id])
            
        return SessionSummaryResponse(session_id=session_id)

session_repo = SessionRepository()
