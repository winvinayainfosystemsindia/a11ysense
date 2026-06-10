"""
Common constants package.
"""
from .wcag import WCAG_CRITERIA_MAP, IMPACT_TO_LEVEL, IMPACT_TO_SEVERITY, parse_wcag_tags

__all__ = [
    "WCAG_CRITERIA_MAP",
    "IMPACT_TO_LEVEL",
    "IMPACT_TO_SEVERITY",
    "parse_wcag_tags",
]
