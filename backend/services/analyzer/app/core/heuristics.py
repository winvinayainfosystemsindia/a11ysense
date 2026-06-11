import re
import logging
from typing import List, Dict, Any
from app.schemas.audit import Violation

logger = logging.getLogger(__name__)

# Heuristics Patterns for False Positive Screening
HIDDEN_PATTERNS = [
    re.compile(r'aria-hidden\s*=\s*["\']true["\']', re.IGNORECASE),
    re.compile(r'display\s*:\s*none', re.IGNORECASE),
    re.compile(r'visibility\s*:\s*hidden', re.IGNORECASE),
    re.compile(r'\btype\s*=\s*["\']hidden["\']', re.IGNORECASE),
    re.compile(r'\bhidden\b', re.IGNORECASE)
]

DEV_PATTERNS = [
    re.compile(r'webpack-dev-server', re.IGNORECASE),
    re.compile(r'__next-prerender', re.IGNORECASE),
    re.compile(r'__next-route-announcer', re.IGNORECASE),
    re.compile(r'react-devtools', re.IGNORECASE)
]

def is_node_hidden(node: Dict[str, Any]) -> bool:
    """
    Checks if the HTML node is hidden from assistive technology or visual display.
    """
    html = node.get("html", "")
    target = str(node.get("target", ""))
    
    # 1. Check HTML attributes and style substrings
    for pattern in HIDDEN_PATTERNS:
        if pattern.search(html) or pattern.search(target):
            return True
            
    # 2. Check inline styles in node properties if present
    style = node.get("style", {})
    if isinstance(style, dict):
        display = str(style.get("display", "")).lower()
        visibility = str(style.get("visibility", "")).lower()
        if display == "none" or visibility == "hidden":
            return True
            
    return False

def is_node_decorative_spacer(node: Dict[str, Any]) -> bool:
    """
    Checks if the element is purely a visual decorative spacer element
    without text or semantic accessibility bindings.
    """
    html = node.get("html", "")
    # Check if empty presentation tag e.g. <div class="spacer" role="presentation"></div>
    if 'role="presentation"' in html or 'role="none"' in html:
        # If there's no visible inner content
        stripped_tags = re.sub(r'<[^>]*>', '', html).strip()
        if not stripped_tags:
            return True
            
    # Pure empty visual tags (e.g. spacer div or span height hacks)
    if html.startswith('<div') or html.startswith('<span'):
        stripped_tags = re.sub(r'<[^>]*>', '', html).strip()
        if not stripped_tags and 'aria-label' not in html and 'aria-labelledby' not in html:
            return True
            
    return False

def is_dev_only_element(node: Dict[str, Any]) -> bool:
    """
    Filters out hot-reloading dev overlays, test indicators, or route announcers.
    """
    html = node.get("html", "")
    target = str(node.get("target", ""))
    
    for pattern in DEV_PATTERNS:
        if pattern.search(html) or pattern.search(target):
            return True
            
    return False

def filter_false_positives(nodes: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Applies heuristic screening rules to filter out automated false positives.
    """
    filtered = []
    for node in nodes:
        # Screen out nodes that are hidden, pure empty decorative spacers, or local dev tools
        if is_node_hidden(node):
            logger.info(f"Heuristics: Filtered hidden node: {node.get('html', '')[:80]}")
            continue
        if is_node_decorative_spacer(node):
            logger.info(f"Heuristics: Filtered decorative spacer node: {node.get('html', '')[:80]}")
            continue
        if is_dev_only_element(node):
            logger.info(f"Heuristics: Filtered local development node: {node.get('html', '')[:80]}")
            continue
        filtered.append(node)
    return filtered

def aggregate_and_deduplicate(violations: List[Violation]) -> List[Violation]:
    """
    De-duplicates and merges similar compliance violations across multiple scanned pages.
    Groups issues by Rule ID and eliminates identical node targets.
    """
    grouped_violations: Dict[str, Violation] = {}
    
    for v in violations:
        # Apply pre-filtering heuristics to nodes
        filtered_nodes = filter_false_positives(v.nodes)
        if not filtered_nodes:
            # If all nodes under this violation are filtered out, discard the rule violation
            continue
            
        if v.id not in grouped_violations:
            # Initialize a new Violation object with filtered nodes
            grouped_violations[v.id] = Violation(
                id=v.id,
                impact=v.impact,
                description=v.description,
                help=v.help,
                helpUrl=v.helpUrl,
                nodes=[],
                metadata=v.metadata.copy()
            )
            
        target_violation = grouped_violations[v.id]
        
        # Merge nodes while avoiding duplicates
        existing_signatures = {
            (node.get("page_url", ""), str(node.get("target", "")), node.get("html", ""))
            for node in target_violation.nodes
        }
        
        for node in filtered_nodes:
            node_signature = (node.get("page_url", ""), str(node.get("target", "")), node.get("html", ""))
            if node_signature not in existing_signatures:
                target_violation.nodes.append(node)
                existing_signatures.add(node_signature)
                
    # Sort de-duplicated violations alphabetically by Rule ID for readability
    return sorted(grouped_violations.values(), key=lambda v: v.id)
