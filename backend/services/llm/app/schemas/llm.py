from pydantic import BaseModel, Field
from typing import Optional, Dict

class GenerateRequest(BaseModel):
    prompt: str = Field(..., description="Prompt payload for LLM completion")
    system_message: Optional[str] = Field(default="", description="Optional system role description")
    session_id: Optional[str] = Field(default=None, description="Correlation ID for token usage tracking")
    provider: Optional[str] = Field(default=None, description="Specific LLM provider override (groq|claude|gemini|mock)")
    model: Optional[str] = Field(default=None, description="Specific model override")
    temperature: float = Field(default=0.1, ge=0.0, le=2.0, description="Sampling temperature")
    max_tokens: int = Field(default=2048, ge=1, le=4096, description="Max response length limit")
    agent_type: Optional[str] = Field(default=None, description="The agent type making the request (e.g., manager, auditor)")

class GenerateResponse(BaseModel):
    text: str = Field(..., description="LLM generated completion")
    provider: str = Field(..., description="Actual provider that served the completion")
    model: str = Field(..., description="Actual model that served the completion")
    input_tokens: int = Field(default=0, description="Input tokens used")
    output_tokens: int = Field(default=0, description="Output tokens generated")
    total_tokens: int = Field(default=0, description="Total tokens consumed")
    estimated_cost_usd: float = Field(default=0.0, description="Estimated dollar cost for the request")
    fallback_occurred: bool = Field(default=False, description="Flag indicating if secondary provider fallback was triggered")
    cached: bool = Field(default=False, description="Flag indicating if request was resolved via Cache")

class AgentTokenStats(BaseModel):
    provider: str = Field(..., description="LLM provider name")
    calls: int = Field(default=0, description="Total number of LLM calls")
    tokens_sent: int = Field(default=0, description="Total tokens sent (input)")
    tokens_received: int = Field(default=0, description="Total tokens received (output)")
    tokens_total: int = Field(default=0, description="Total tokens utilized")

class SessionSummaryResponse(BaseModel):
    session_id: str = Field(..., description="The session tracking ID")
    total_requests: int = Field(default=0, description="Total completed LLM requests")
    total_input_tokens: int = Field(default=0, description="Cumulative input tokens consumed")
    total_output_tokens: int = Field(default=0, description="Cumulative output tokens consumed")
    total_tokens: int = Field(default=0, description="Cumulative total tokens consumed")
    total_cost_usd: float = Field(default=0.0, description="Cumulative cost in USD")
    provider_breakdown: Dict[str, int] = Field(default_factory=dict, description="Number of LLM requests grouped by provider name")
    provider: Optional[str] = Field(default=None, description="The primary provider utilized in the session")
    breakdown: Dict[str, AgentTokenStats] = Field(default_factory=dict, description="Token usage breakdown per agent type")

