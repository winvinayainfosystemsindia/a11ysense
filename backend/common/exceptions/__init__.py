from datetime import datetime
from typing import Dict, Any, Optional
from common.utils.correlation import get_correlation_id

class A11ySenseBaseException(Exception):
    """
    Parent class for all custom A11ySense AI compliance errors.
    Carries tracking context across the distributed microservices.
    """
    def __init__(
        self,
        message: str,
        service_name: str,
        correlation_id: Optional[str] = None,
        severity: str = "error",
        context: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message)
        self.message = message
        self.service_name = service_name
        self.correlation_id = correlation_id or get_correlation_id()
        self.severity = severity.lower()
        self.timestamp = datetime.utcnow()
        self.context = context or {}

    def to_dict(self) -> Dict[str, Any]:
        """
        Serializes error parameters to standard dictionary payload.
        """
        return {
            "error": True,
            "message": self.message,
            "service_name": self.service_name,
            "correlation_id": self.correlation_id,
            "severity": self.severity,
            "timestamp": self.timestamp.isoformat(),
            "context": self.context
        }

# Domain-Specific Exception Subclasses
class GatewayException(A11ySenseBaseException):
    def __init__(self, message: str, severity: str = "error", context: Optional[Dict[str, Any]] = None):
        super().__init__(message, "gateway-service", severity=severity, context=context)

class CrawlerException(A11ySenseBaseException):
    def __init__(self, message: str, severity: str = "error", context: Optional[Dict[str, Any]] = None):
        super().__init__(message, "crawler-service", severity=severity, context=context)

class AgentException(A11ySenseBaseException):
    def __init__(self, message: str, severity: str = "error", context: Optional[Dict[str, Any]] = None):
        super().__init__(message, "agent-service", severity=severity, context=context)

class LLMException(A11ySenseBaseException):
    def __init__(self, message: str, severity: str = "error", context: Optional[Dict[str, Any]] = None):
        super().__init__(message, "llm-service", severity=severity, context=context)

class AnalyzerException(A11ySenseBaseException):
    def __init__(self, message: str, severity: str = "error", context: Optional[Dict[str, Any]] = None):
        super().__init__(message, "analyzer-service", severity=severity, context=context)

class ReportingException(A11ySenseBaseException):
    def __init__(self, message: str, severity: str = "error", context: Optional[Dict[str, Any]] = None):
        super().__init__(message, "reporting-service", severity=severity, context=context)
