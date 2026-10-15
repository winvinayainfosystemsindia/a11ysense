"""
LLM usage & cost tracking.

Every LLM API call made while an audit runs is recorded (provider, model, tokens,
cost in USD) against the audit's task id, so the cost of Claude and Gemini can be
reported separately.

Prices are USD per 1,000,000 tokens and can be overridden without code changes via
the LLM_PRICING_JSON env var, e.g.
    LLM_PRICING_JSON='{"claude-sonnet-4-6": [3.0, 15.0], "gemini-3.5-flash": [1.5, 9.0]}'
"""
import contextvars
import json
import logging
import os
from typing import Any, Dict, Optional, Tuple

logger = logging.getLogger(__name__)

# model -> (input $/1M tokens, output $/1M tokens)
DEFAULT_PRICING: Dict[str, Tuple[float, float]] = {
    "claude-sonnet-4-6": (3.00, 15.00),
    "gemini-3.5-flash-lite": (0.30, 2.50),
    "gemini-3.5-flash": (1.50, 9.00),
    "llama-3.1-8b-instant": (0.05, 0.08),
}
# Used when a model name is not in the table.
PROVIDER_FALLBACK_PRICING: Dict[str, Tuple[float, float]] = {
    "claude": (3.00, 15.00),
    "gemini": (1.50, 9.00),
    "groq": (0.05, 0.08),
}

PROVIDER_LABELS = {"claude": "Claude Sonnet", "gemini": "Gemini", "groq": "Groq"}

_current_task: contextvars.ContextVar = contextvars.ContextVar("llm_usage_task_id", default=None)


def set_current_task(task_id: Optional[str]) -> None:
    """Attach all LLM calls made in this async context to an audit task id."""
    _current_task.set(task_id)


def get_current_task() -> Optional[str]:
    return _current_task.get()


def _pricing_table() -> Dict[str, Tuple[float, float]]:
    table = dict(DEFAULT_PRICING)
    raw = os.getenv("LLM_PRICING_JSON")
    if raw:
        try:
            for model, pair in json.loads(raw).items():
                table[model] = (float(pair[0]), float(pair[1]))
        except Exception as e:
            logger.warning(f"Invalid LLM_PRICING_JSON ignored: {e}")
    return table


CATEGORY_LABELS: Dict[str, str] = {
    "defect": "Defect Remediation & Analysis",
    "testcase": "Test Case Synthesis & Evaluation",
    "other": "Other Operations (Planning, Summary, Vision)",
}


def compute_cost(provider: str, model: str, input_tokens: int, output_tokens: int) -> float:
    price_in, price_out = _pricing_table().get(model) or PROVIDER_FALLBACK_PRICING.get(provider, (0.0, 0.0))
    return (input_tokens * price_in + output_tokens * price_out) / 1_000_000


def record_call(
    provider: str,
    model: str,
    input_tokens: int,
    output_tokens: int,
    cached: bool = False,
    task_id: Optional[str] = None,
    category: str = "other",
) -> None:
    """Persist one LLM call with its operational category (defect, testcase, other)."""
    task_id = task_id or get_current_task()
    if not task_id:
        return
    cat = (category or "other").strip().lower()
    if cat not in CATEGORY_LABELS:
        cat = "other"
    try:
        from common.database.connection import get_session_local
        from common.database.models import LLMUsage

        cost = 0.0 if cached else compute_cost(provider, model, input_tokens or 0, output_tokens or 0)
        db = get_session_local()()
        try:
            db.add(LLMUsage(
                task_id=task_id,
                provider=provider,
                model=model,
                input_tokens=int(input_tokens or 0),
                output_tokens=int(output_tokens or 0),
                cached=bool(cached),
                cost_usd=cost,
                category=cat,
            ))
            db.commit()
        finally:
            db.close()
    except Exception as e:
        logger.warning(f"Failed to record LLM usage for task {task_id}: {e}")


def summarize(task_id: str) -> Dict[str, Any]:
    """Aggregate recorded LLM usage for a task, split by provider, model, and category (defect, testcase, other)."""
    from common.database.connection import get_session_local
    from common.database.models import LLMUsage

    by_provider: Dict[str, Dict[str, Any]] = {}
    by_model: Dict[str, Dict[str, Any]] = {}
    # Pre-populate all standard categories so frontend always has clean keys
    by_category: Dict[str, Dict[str, Any]] = {
        cat: {
            "category": cat,
            "label": label,
            "calls": 0,
            "cached_calls": 0,
            "input_tokens": 0,
            "output_tokens": 0,
            "total_tokens": 0,
            "cost_usd": 0.0,
        }
        for cat, label in CATEGORY_LABELS.items()
    }
    matrix_map: Dict[Tuple[str, str, str], Dict[str, Any]] = {}

    db = get_session_local()()
    try:
        rows = db.query(LLMUsage).filter(LLMUsage.task_id == task_id).all()
    finally:
        db.close()

    def _bucket(store, key, extra=None):
        if key not in store:
            store[key] = {
                "calls": 0, "cached_calls": 0, "input_tokens": 0, "output_tokens": 0,
                "total_tokens": 0, "cost_usd": 0.0, **(extra or {}),
            }
        return store[key]

    for r in rows:
        cat = (getattr(r, "category", None) or "other").strip().lower()
        if cat not in by_category:
            cat = "other"

        # Bucket by provider
        bp = _bucket(by_provider, r.provider, {"label": PROVIDER_LABELS.get(r.provider, r.provider)})
        # Bucket by model
        bm = _bucket(by_model, r.model, {"provider": r.provider})
        # Bucket by category
        bc = by_category[cat]

        # Matrix key: (category, provider, model)
        mkey = (cat, r.provider, r.model)
        if mkey not in matrix_map:
            matrix_map[mkey] = {
                "category": cat,
                "category_label": CATEGORY_LABELS.get(cat, cat.title()),
                "provider": r.provider,
                "provider_label": PROVIDER_LABELS.get(r.provider, r.provider.title()),
                "model": r.model,
                "calls": 0,
                "cached_calls": 0,
                "input_tokens": 0,
                "output_tokens": 0,
                "total_tokens": 0,
                "cost_usd": 0.0,
            }
        bmat = matrix_map[mkey]

        if r.cached:
            bp["cached_calls"] += 1
            bm["cached_calls"] += 1
            bc["cached_calls"] += 1
            bmat["cached_calls"] += 1
            continue

        in_tok = int(r.input_tokens or 0)
        out_tok = int(r.output_tokens or 0)
        cost = float(r.cost_usd or 0.0)

        for b in (bp, bm, bc, bmat):
            b["calls"] += 1
            b["input_tokens"] += in_tok
            b["output_tokens"] += out_tok
            b["total_tokens"] += in_tok + out_tok
            b["cost_usd"] += cost

    for store in (by_provider, by_model, by_category):
        for b in store.values():
            b["cost_usd"] = round(b["cost_usd"], 6)

    matrix = list(matrix_map.values())
    for item in matrix:
        item["cost_usd"] = round(item["cost_usd"], 6)

    totals = {
        "calls": sum(b["calls"] for b in by_provider.values()),
        "cached_calls": sum(b["cached_calls"] for b in by_provider.values()),
        "input_tokens": sum(b["input_tokens"] for b in by_provider.values()),
        "output_tokens": sum(b["output_tokens"] for b in by_provider.values()),
        "cost_usd": round(sum(b["cost_usd"] for b in by_provider.values()), 6),
    }
    totals["total_tokens"] = totals["input_tokens"] + totals["output_tokens"]

    return {
        "task_id": task_id,
        "by_provider": by_provider,
        "by_category": by_category,
        "by_model": by_model,
        "matrix": matrix,
        "totals": totals,
    }
