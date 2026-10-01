"""
Element Context Capture Skill for A11ySense AI.
Collects precise contextual facts about where an element sits on the page
to generate accurate, step-by-step screen reader navigation instructions.
"""
import html as html_lib
import re
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)


def extract_context_from_html(html_str: str) -> Dict[str, Any]:
    """
    Parses an HTML snippet string directly without a browser DOM.
    Accurately extracts:
      tag, role, visible_text, aria_label, accessible_name,
      clean_name, tabindex, href, is_menu_item, type_name, friendly_label
    """
    if not html_str or not isinstance(html_str, str):
        return {}

    snippet = html_str.strip()
    tag_match = re.match(r"^<([a-zA-Z0-9]+)", snippet)
    tag = tag_match.group(1).lower() if tag_match else ""

    role_m = re.search(r'\brole=["\']([^"\']+)["\']', snippet, re.IGNORECASE)
    role = role_m.group(1).lower() if role_m else ""

    aria_m = re.search(r'\baria-label=["\']([^"\']+)["\']', snippet, re.IGNORECASE)
    aria_label = html_lib.unescape(aria_m.group(1).strip()) if aria_m else ""

    alt_m = re.search(r'\balt=["\']([^"\']+)["\']', snippet, re.IGNORECASE)
    alt = html_lib.unescape(alt_m.group(1).strip()) if alt_m else ""

    title_m = re.search(r'\btitle=["\']([^"\']+)["\']', snippet, re.IGNORECASE)
    title = html_lib.unescape(title_m.group(1).strip()) if title_m else ""

    tab_m = re.search(r'\btabindex=["\']([^"\']+)["\']', snippet, re.IGNORECASE)
    tabindex = tab_m.group(1).strip() if tab_m else ""

    href_m = re.search(r'\bhref=["\']([^"\']+)["\']', snippet, re.IGNORECASE)
    href = href_m.group(1).strip() if href_m else ""

    # Extract text content between opening and closing tags, stripping nested tags
    inner = re.sub(r'<[^>]+>', ' ', snippet)
    visible_text = html_lib.unescape(" ".join(inner.split())).strip()

    # Determine best accessible name
    accessible_name = aria_label or alt or title or visible_text

    is_menu_item = (
        role == "menuitem"
        or "menuitem" in role
        or (tag == "a" and tabindex == "-1" and ("menu" in href or "nav" in snippet.lower()))
    )

    if is_menu_item:
        type_name = "link in the menu" if (tag == "a" or href) else "menu item"
    elif role == "button" or tag == "button":
        type_name = "button"
    elif role == "link" or tag == "a":
        type_name = "link"
    elif role == "tab":
        type_name = "tab"
    elif tag in ("input", "select", "textarea"):
        type_name = "form field"
    elif tag == "img" or role == "img":
        type_name = "picture"
    elif tag in ("h1", "h2", "h3", "h4", "h5", "h6"):
        type_name = "heading"
    else:
        type_name = "interactive control"

    raw_name = visible_text or accessible_name or ""
    # Clean up trailing ", link" or ", button" from screen-reader style labels (e.g. "F&O, link" -> "F&O")
    clean_name = re.sub(r',\s*(link|button|menuitem|dropdown)\s*$', '', raw_name, flags=re.IGNORECASE).strip()

    if clean_name:
        friendly_label = f"the '{clean_name}' {type_name}"
    else:
        friendly_label = f"the {type_name}"

    return {
        "tag": tag,
        "role": role,
        "aria_label": aria_label,
        "visible_text": visible_text,
        "accessible_name": accessible_name,
        "clean_name": clean_name,
        "tabindex": tabindex,
        "href": href,
        "is_menu_item": is_menu_item,
        "type_name": type_name,
        "friendly_label": friendly_label,
    }


def quick_key_for(ctx: Optional[Dict[str, Any]]) -> str:
    """
    Returns the screen reader single-letter navigation quick key for an element.
    button -> B
    link -> K
    input/select/textarea -> F
    img -> G
    heading -> H
    landmark -> D in NVDA / R in JAWS
    table -> T
    list -> L
    otherwise -> Tab
    """
    if not ctx or not isinstance(ctx, dict):
        return "Tab"

    tag = str(ctx.get("tag", "")).lower()
    role = str(ctx.get("role", "")).lower()

    if role == "button" or tag == "button":
        return "B"
    elif role == "link" or tag == "a":
        return "K"
    elif tag in ("input", "select", "textarea") or role in ("textbox", "combobox", "checkbox", "radio", "listbox"):
        return "F"
    elif tag == "img" or role == "img":
        return "G"
    elif tag in ("h1", "h2", "h3", "h4", "h5", "h6") or role == "heading":
        return "H"
    elif role in ("banner", "main", "navigation", "contentinfo", "complementary", "region"):
        return "D in NVDA / R in JAWS"
    elif tag == "table" or role in ("table", "grid"):
        return "T"
    elif tag in ("ul", "ol") or role == "list":
        return "L"
    return "Tab"


def format_element_context(ctx: Optional[Dict[str, Any]]) -> str:
    """
    Formats element context into 4 to 6 plain bullet lines for the {element_context} placeholder.
    Each item is '(not captured)' if unknown.
    """
    if not ctx or not isinstance(ctx, dict):
        return (
            "- Landmark section: (not captured)\n"
            "- Nearest heading above it: (not captured)\n"
            "- Position inside section: (not captured)\n"
            "- Keyboard Tab presses from top of page: (not captured)"
        )

    # Landmark
    landmark = ctx.get("landmark")
    if isinstance(landmark, dict) and landmark.get("role"):
        l_label = f" ('{landmark['label']}')" if landmark.get("label") else ""
        landmark_str = f"{landmark['role']}{l_label}"
    else:
        landmark_str = "(not captured)"

    # Nearest heading
    heading = ctx.get("nearest_heading")
    if isinstance(heading, dict) and heading.get("text"):
        h_lvl = f"H{heading.get('level')}" if heading.get("level") else "Heading"
        heading_str = f"{h_lvl}: '{heading['text']}'"
    else:
        heading_str = "(not captured)"

    # Position
    pos = ctx.get("position")
    if isinstance(pos, dict) and pos.get("index") is not None and pos.get("total") is not None:
        position_str = f"item {pos['index']} of {pos['total']}"
    else:
        position_str = "(not captured)"

    # Tab stops
    tab_stops = ctx.get("tab_stops_from_top")
    tab_str = f"approximately {tab_stops} Tab press(es)" if tab_stops is not None else "(not captured)"

    lines = [
        f"- Landmark section: {landmark_str}",
        f"- Nearest heading above it: {heading_str}",
        f"- Position inside section: {position_str}",
        f"- Keyboard Tab presses from top of page: {tab_str}",
    ]

    vis_text = ctx.get("visible_text")
    if vis_text:
        lines.append(f"- Visible text: '{vis_text}'")

    acc_name = ctx.get("accessible_name")
    if acc_name and acc_name != vis_text:
        lines.append(f"- Spoken name: '{acc_name}'")

    return "\n".join(lines)


async def collect_element_context(page, selector: str) -> Dict[str, Any]:
    """
    Collects contextual information for an element using one page.evaluate call.
    Returns: tag, role, accessible_name, visible_text, landmark, nearest_heading,
             position, tab_stops_from_top, is_visible.
    Returns {} on any failure. Never raises.
    """
    if not page or not selector:
        return {}

    try:
        data = await page.evaluate("""(sel) => {
            try {
                // Reject bare tag selectors without id, class, or attribute, as they wrongly match top-of-page elements
                const trimmed = (sel || '').trim();
                if (/^[a-zA-Z0-9]+$/.test(trimmed) && !['main', 'header', 'footer', 'nav'].includes(trimmed.toLowerCase())) {
                    return {};
                }
                let el = null;
                try {
                    el = document.querySelector(sel);
                } catch(e) {}
                if (!el) return {};

                const tag = el.tagName.toLowerCase();
                const role = el.getAttribute('role') || el.computedRole || tag;
                const visibleText = (el.innerText || el.textContent || '').trim().substring(0, 80);
                const accessibleName = el.getAttribute('aria-label') || el.getAttribute('alt') || el.getAttribute('title') || visibleText;

                // 1. Nearest landmark ancestor
                const landmarkTags = ['header', 'nav', 'main', 'footer', 'aside', 'section', 'form'];
                let landmark = null;
                let parent = el.parentElement;
                while (parent && parent !== document.body) {
                    const pRole = parent.getAttribute('role');
                    const pTag = parent.tagName.toLowerCase();
                    if (['banner', 'navigation', 'main', 'contentinfo', 'complementary', 'region'].includes(pRole) || landmarkTags.includes(pTag)) {
                        const lRole = pRole || (pTag === 'header' ? 'banner' : pTag === 'footer' ? 'contentinfo' : pTag === 'nav' ? 'navigation' : pTag);
                        const lLabel = parent.getAttribute('aria-label') || parent.getAttribute('title') || '';
                        landmark = { role: lRole, label: lLabel };
                        break;
                    }
                    parent = parent.parentElement;
                }

                // 2. Nearest heading before element in DOM order
                let nearestHeading = null;
                const headings = Array.from(document.querySelectorAll('h1, h2, h3, h4, h5, h6, [role="heading"]'));
                for (let i = headings.length - 1; i >= 0; i--) {
                    const h = headings[i];
                    if (h.compareDocumentPosition(el) & Node.DOCUMENT_POSITION_FOLLOWING) {
                        const text = (h.innerText || h.textContent || '').trim().substring(0, 60);
                        const level = h.getAttribute('aria-level') || (h.tagName.match(/h([1-6])/i) ? RegExp.$1 : '2');
                        nearestHeading = { level: parseInt(level) || 2, text: text };
                        break;
                    }
                }

                // 3. Position among same role inside same landmark / parent container
                const container = parent || document.body;
                const siblings = Array.from(container.querySelectorAll(tag));
                const index = siblings.indexOf(el) + 1;
                const total = siblings.length;
                const position = { index: index, total: total };

                // 4. Tab stops from top
                const focusables = Array.from(document.querySelectorAll('a[href], button:not([disabled]), input:not([disabled]), select:not([disabled]), textarea:not([disabled]), [tabindex]:not([tabindex="-1"])'));
                const tabIndex = focusables.indexOf(el);
                const tabStops = tabIndex >= 0 ? tabIndex + 1 : focusables.filter(f => (f.compareDocumentPosition(el) & Node.DOCUMENT_POSITION_FOLLOWING)).length;

                // 5. Visibility
                const rect = el.getBoundingClientRect();
                const isVisible = rect.width > 0 && rect.height > 0 && window.getComputedStyle(el).display !== 'none';

                return {
                    tag: tag,
                    role: role,
                    accessible_name: accessibleName,
                    visible_text: visibleText,
                    landmark: landmark,
                    nearest_heading: nearestHeading,
                    position: position,
                    tab_stops_from_top: tabStops,
                    is_visible: isVisible
                };
            } catch (err) {
                return {};
            }
        }""", selector)
        return data or {}
    except Exception as e:
        logger.debug(f"collect_element_context failed for '{selector}': {e}")
        return {}
