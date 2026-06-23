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

def _element_signature(node: Dict[str, Any]) -> str:
    """
    Identifies whether a violating node is the *same physical element* as another,
    regardless of which page it was found on (e.g. a shared nav/footer element
    repeated verbatim across pages). Falls back to the target selector when no
    HTML snippet is available.
    """
    html = re.sub(r'\s+', ' ', node.get("html", "") or "").strip()
    if html:
        return html
    return str(node.get("target", ""))


def aggregate_and_deduplicate(violations: List[Violation]) -> List[Violation]:
    """
    De-duplicates and groups compliance violations.

    Violations are grouped by (rule_id, element signature) rather than rule_id
    alone. This means:
    - The SAME element (identical HTML/selector) repeated across multiple pages
      — e.g. a shared nav/footer component — is consolidated into ONE violation
      whose nodes span every affected page (recorded in metadata["affected_pages"]).
    - The same rule firing on DIFFERENT content on different pages produces
      SEPARATE violation objects, one per distinct element, so each page gets
      its own clearly-attributed defect rather than being folded into a single
      cross-page entry.
    """
    grouped_violations: Dict[tuple, Violation] = {}

    for v in violations:
        # Apply pre-filtering heuristics to nodes
        filtered_nodes = filter_false_positives(v.nodes)
        if not filtered_nodes:
            # If all nodes under this violation are filtered out, discard the rule violation
            continue

        # Partition this violation's nodes by element signature — a single
        # axe-core/skill violation can already bundle multiple distinct elements.
        nodes_by_signature: Dict[str, List[Dict[str, Any]]] = {}
        for node in filtered_nodes:
            sig = _element_signature(node)
            nodes_by_signature.setdefault(sig, []).append(node)

        for sig, sig_nodes in nodes_by_signature.items():
            group_key = (v.id, sig)
            if group_key not in grouped_violations:
                grouped_violations[group_key] = Violation(
                    id=v.id,
                    impact=v.impact,
                    description=v.description,
                    help=v.help,
                    helpUrl=v.helpUrl,
                    nodes=[],
                    metadata=v.metadata.copy()
                )

            target_violation = grouped_violations[group_key]

            # Merge nodes while avoiding duplicates (e.g. the same element
            # re-detected on the same page across keyboard/screen-reader/axe passes)
            existing_signatures = {
                (node.get("page_url", ""), str(node.get("target", "")))
                for node in target_violation.nodes
            }

            for node in sig_nodes:
                node_signature = (node.get("page_url", ""), str(node.get("target", "")))
                if node_signature not in existing_signatures:
                    target_violation.nodes.append(node)
                    existing_signatures.add(node_signature)

    # Record which pages each violation affects, so a violation spanning
    # multiple pages (shared component) can be displayed/reported as such.
    for violation in grouped_violations.values():
        affected_pages = sorted({
            node.get("page_url", "") for node in violation.nodes if node.get("page_url")
        })
        violation.metadata["affected_pages"] = affected_pages

    # Sort de-duplicated violations alphabetically by Rule ID for readability
    return sorted(grouped_violations.values(), key=lambda v: v.id)
