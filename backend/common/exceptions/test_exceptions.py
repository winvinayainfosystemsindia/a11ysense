import pytest
import json
import time
from common.utils.correlation import get_correlation_id, set_correlation_id, get_correlation_headers
from common.exceptions import A11ySenseBaseException, GatewayException, CrawlerException, LLMException
from common.exceptions.alerting import evaluate_alert_rules

def test_correlation_id_contextvars():
    """
    Validates async-safe correlation ID binding and propagation headers.
    """
    # Test auto-generation
    cid1 = get_correlation_id()
    assert cid1 is not None
    assert len(cid1) > 10
    
    # Test custom binding
    set_correlation_id("test-correlation-uuid")
    assert get_correlation_id() == "test-correlation-uuid"
    
    # Test headers mapping
    headers = get_correlation_headers()
    assert headers["X-Correlation-ID"] == "test-correlation-uuid"

def test_standard_exception_serialization():
    """
    Validates serialization properties of base and subclass exceptions.
    """
    set_correlation_id("serialized-trace-id")
    
    # Base Exception
    base_err = A11ySenseBaseException(
        message="Failure context",
        service_name="custom-service",
        severity="warning",
        context={"custom_key": 42}
    )
    
    serialized = base_err.to_dict()
    assert serialized["error"] is True
    assert serialized["message"] == "Failure context"
    assert serialized["service_name"] == "custom-service"
    assert serialized["severity"] == "warning"
    assert serialized["correlation_id"] == "serialized-trace-id"
    assert serialized["context"]["custom_key"] == 42
    
    # Subclass Domain exception (Gateway)
    gate_err = GatewayException(message="Invalid route parameters")
    gate_serialized = gate_err.to_dict()
    assert gate_serialized["service_name"] == "gateway-service"
    assert gate_serialized["severity"] == "error"

def test_alerting_rules_engine(capsys):
    """
    Validates alert channel dispatches and sliding window counter thresholds.
    """
    # 1. Critical Anomaly Trigger
    crit_event = {
        "message": "Playwright web driver crash",
        "service_name": "agent-service",
        "severity": "critical",
        "correlation_id": "critical-trace-id",
        "timestamp": "2026-05-25T12:00:00",
        "context": {}
    }
    
    evaluate_alert_rules(crit_event)
    captured = capsys.readouterr()
    assert "🚨 [A11YSENSE ALERT] RULE TRIGGERED: CRITICAL FAULT ANOMALY" in captured.out
    assert "📧 [ALERT EMAIL SENT]" in captured.out
    assert "💬 [SLACK WEBHOOK POSTED]" in captured.out
    
    # 2. LLM Exception Rate sliding window check
    llm_event = {
        "message": "Groq rate limit reached",
        "service_name": "llm-service",
        "severity": "error",
        "correlation_id": "llm-trace-id",
        "timestamp": "2026-05-25T12:00:00",
        "context": {"exception_type": "LLMException"}
    }
    
    # Send 5 events (under the limit of >5)
    for _ in range(5):
        evaluate_alert_rules(llm_event)
        
    captured_under = capsys.readouterr()
    assert "LLM EXCEPTION RATE EXCEEDED" not in captured_under.out
    
    # Send the 6th event (trigger > 5 alert!)
    evaluate_alert_rules(llm_event)
    captured_over = capsys.readouterr()
    assert "🚨 [A11YSENSE ALERT] RULE TRIGGERED: LLM EXCEPTION RATE EXCEEDED" in captured_over.out
