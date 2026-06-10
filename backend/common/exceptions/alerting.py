import time
import logging
from typing import Dict, Any, List

logger = logging.getLogger(__name__)

# Sliding window storage for LLM Exception rates
_llm_exception_timestamps: List[float] = []

def trigger_alert_channels(event: Dict[str, Any], rule_name: str) -> None:
    """
    Simulates production alerting channels (Console, Slack Webhooks, Email Alerts).
    In an enterprise cluster, this hooks into Sentry, PagerDuty, or SMTP relays.
    """
    msg = event.get("message", "No message provided")
    service = event.get("service_name", "unknown")
    severity = event.get("severity", "error")
    correlation_id = event.get("correlation_id", "N/A")
    
    # 1. Standard structured logging
    alert_banner = f"""
================================================================================
🚨 [A11YSENSE ALERT] RULE TRIGGERED: {rule_name}
--------------------------------------------------------------------------------
Service:    {service.upper()}
Severity:   {severity.upper()}
Error:      {msg}
Correlation ID: {correlation_id}
Timestamp:  {event.get("timestamp")}
================================================================================
"""
    logger.critical(alert_banner)
    print(alert_banner)
    
    # 2. Mock Production Outlets
    # Slack Webhook Mock
    slack_webhook_url = "https://slack.com/mock-webhook-url-disabled"
    print(f"📧 [ALERT EMAIL SENT] Recipient: support@winvinaya.com | Subject: [CRITICAL ALERT] {service.upper()} Fault - {correlation_id}")
    print(f"💬 [SLACK WEBHOOK POSTED] Channel: #accessibility-alerts | Endpoint: {slack_webhook_url}")

def evaluate_alert_rules(event: Dict[str, Any]) -> None:
    """
    Evaluates real-time threshold metrics and anomaly conditions against incoming errors.
    """
    global _llm_exception_timestamps
    
    severity = str(event.get("severity", "")).lower()
    service = str(event.get("service_name", "")).lower()
    context = event.get("context", {}) or {}
    exception_type = context.get("exception_type", "")
    
    # Rule 1: Immediate Alert on any CriticalException / Uncaught Crash
    if severity == "critical":
        trigger_alert_channels(event, "CRITICAL FAULT ANOMALY")
        return
        
    # Rule 2: LLMException Frequency rate exceeding 5 faults per 1-minute window
    is_llm_error = "llm" in service or "LLMException" in exception_type
    
    if is_llm_error:
        now = time.time()
        _llm_exception_timestamps.append(now)
        
        # Prune elements older than 60 seconds (1 minute sliding window)
        _llm_exception_timestamps = [t for t in _llm_exception_timestamps if now - t <= 60.0]
        
        if len(_llm_exception_timestamps) > 5:
            # Trigger frequency threshold alert
            trigger_alert_channels(event, f"LLM EXCEPTION RATE EXCEEDED ({len(_llm_exception_timestamps)} errors/min)")
            # Prune to prevent repeated cascade warnings instantly
            _llm_exception_timestamps = []
