from playwright.async_api import Page
from common.schemas.audit import Violation
from pathlib import Path
import logging
import os
import ctypes

logger = logging.getLogger(__name__)

# Resolve storage directory relative to this source file.
# Path: implementations/screen_reader.py → up 6 levels → project root (A11ySense_AI/)
_PROJECT_ROOT = Path(__file__).resolve().parents[6]
_STORAGE_DIR = _PROJECT_ROOT / "axe_library"

class NvdaController:
    """
    Optional NVDA integration — cosmetic only.
    When NVDA is running on the host machine, it speaks the computed announcements
    aloud. The actual screen reader simulation audit is 100% JS DOM inspection
    and does NOT require NVDA to be installed.
    """
    def __init__(self):
        self._dll = None
        try:
            # Resolve DLL path dynamically (works on any machine/container)
            dll_path = str(_STORAGE_DIR / "nvdaControllerClient.dll")
            if os.path.exists(dll_path):
                self._dll = ctypes.windll.LoadLibrary(dll_path)
                logger.info(f"Loaded NVDA controller client DLL from: {dll_path}")
            else:
                # Try system-level NVDA controller (only works if NVDA is installed)
                self._dll = ctypes.windll.nvdaControllerClient
                logger.info("Loaded system NVDA controller client")
        except Exception as e:
            logger.debug(f"NVDA controller client DLL not available (NVDA speech disabled): {e}")


    def is_running(self) -> bool:
        if not self._dll:
            return False
        try:
            return self._dll.nvdaController_testIfRunning() == 0
        except Exception:
            return False

    def speak(self, text: str):
        if not self._dll:
            return
        try:
            self._dll.nvdaController_speakText(text)
        except Exception as e:
            logger.debug(f"Failed to make NVDA speak: {e}")

    def cancel(self):
        if not self._dll:
            return
        try:
            self._dll.nvdaController_cancelSpeech()
        except Exception:
            pass

class ScreenReaderSkill:
    """
    Skill for simulating NVDA/JAWS screen reader announcements and verifying accessibility labels.
    """
    def __init__(self):
        self.nvda = NvdaController()

    async def run_screen_reader_test(self, page: Page) -> dict:
        logger.info("Running Screen Reader Simulation checks")
        
        js_announcement_script = """() => {
            const elements = Array.from(document.querySelectorAll(
                'a[href], area[href], input, select, textarea, button, iframe, object, embed, [tabindex]:not([tabindex="-1"]), [contenteditable], [role="button"], [role="link"], [role="checkbox"], [role="radio"]'
            )).filter(el => {
                const rect = el.getBoundingClientRect();
                if (rect.width === 0 || rect.height === 0) return false;
                const style = window.getComputedStyle(el);
                return style.display !== 'none' && style.visibility !== 'hidden' && style.opacity !== '0';
            });

            function getAnnouncement(el) {
                let role = el.getAttribute("role");
                const tagName = el.tagName.toLowerCase();
                
                if (!role) {
                    if (tagName === "a" && el.hasAttribute("href")) role = "link";
                    else if (tagName === "button") role = "button";
                    else if (tagName === "input") {
                        const type = (el.getAttribute("type") || "text").toLowerCase();
                        if (type === "checkbox") role = "checkbox";
                        else if (type === "radio") role = "radio";
                        else if (type === "submit" || type === "button" || type === "reset") role = "button";
                        else role = "edit";
                    }
                    else if (tagName === "textarea") role = "edit";
                    else if (tagName === "select") role = "combobox";
                    else if (/^h[1-6]$/.test(tagName)) role = "heading";
                    else if (tagName === "img") role = "graphic";
                }
                
                let name = "";
                if (el.getAttribute("aria-labelledby")) {
                    const ids = el.getAttribute("aria-labelledby").split(/\\s+/);
                    const labels = ids.map(id => {
                        const lbl = document.getElementById(id);
                        return lbl ? lbl.innerText || lbl.textContent : "";
                    }).filter(Boolean);
                    if (labels.length > 0) name = labels.join(" ");
                }
                
                if (!name && el.getAttribute("aria-label")) {
                    name = el.getAttribute("aria-label");
                }
                
                if (!name && (tagName === "input" || tagName === "textarea" || tagName === "select")) {
                    if (el.id) {
                        const label = document.querySelector(`label[for="${el.id}"]`);
                        if (label) name = label.innerText || label.textContent;
                    }
                    if (!name) {
                        const parentLabel = el.closest("label");
                        if (parentLabel) {
                            name = Array.from(parentLabel.childNodes)
                                .filter(node => node !== el)
                                .map(node => node.textContent)
                                .join(" ")
                                .trim();
                        }
                    }
                    if (!name && el.getAttribute("placeholder")) {
                        name = el.getAttribute("placeholder");
                    }
                }
                
                if (!name && tagName === "img") {
                    if (el.hasAttribute("alt")) name = el.getAttribute("alt");
                    else if (el.getAttribute("title")) name = el.getAttribute("title");
                }
                
                if (!name && el.getAttribute("title")) {
                    name = el.getAttribute("title");
                }
                
                if (!name) {
                    name = el.innerText || el.textContent || "";
                }
                
                name = name.trim().replace(/\\s+/g, " ");
                
                let state = "";
                if (el.disabled || el.getAttribute("aria-disabled") === "true") {
                    state += " unavailable";
                }
                
                if (role === "checkbox" || role === "radio") {
                    const isChecked = el.checked || el.getAttribute("aria-checked") === "true";
                    state += isChecked ? " checked" : " not checked";
                }
                
                if (el.getAttribute("aria-expanded") === "true") {
                    state += " expanded";
                } else if (el.getAttribute("aria-expanded") === "false") {
                    state += " collapsed";
                }
                
                let value = "";
                if (role === "edit") {
                    value = el.value || el.innerText || "";
                    if (!value) value = "blank";
                } else if (role === "combobox") {
                    value = el.options && el.selectedIndex >= 0 ? el.options[el.selectedIndex].text : (el.value || "");
                }
                
                let announcement = "";
                if (role === "heading") {
                    const level = el.tagName.substring(1) || el.getAttribute("aria-level") || "2";
                    announcement = `${name} heading level ${level}`;
                } else if (role === "link") {
                    announcement = `${name} link`;
                } else if (role === "button") {
                    announcement = `${name} button`;
                } else if (role === "checkbox") {
                    announcement = `${name} checkbox${state}`;
                } else if (role === "radio") {
                    announcement = `${name} radio button${state}`;
                } else if (role === "edit") {
                    announcement = `${name} edit ${value}${state}`;
                } else if (role === "combobox") {
                    announcement = `${name} combobox ${value}${state}`;
                } else if (role === "graphic") {
                    if (el.getAttribute("alt") === "") announcement = "";
                    else announcement = `${name} graphic`;
                } else {
                    announcement = `${name} ${role || ""}`.trim();
                }
                
                const className = (el.className || "").toString().toLowerCase();
                const idName = (el.id || "").toLowerCase();
                const textLower = (el.innerText || el.getAttribute('aria-label') || "").toLowerCase();
                
                const hasDropdownText = textLower.includes("dropdown") || textLower.includes("menu") || 
                                         textLower.includes("submenu") || textLower.includes("select");
                
                const hasArrowChar = /[▼▾⌄⌵🛆🛆˯]/.test(textLower);
                
                const hasDropdownClassOrId = className.includes("dropdown") || idName.includes("dropdown") ||
                                             className.includes("menu-toggle") || idName.includes("menu-toggle") ||
                                             className.includes("has-submenu") || className.includes("submenu") ||
                                             className.includes("nav-link") || className.includes("nav-item") ||
                                             className.includes("menu-item") || className.includes("navbar") ||
                                             className.includes("menu-link");
                                             
                let hasSvgOrIconChild = false;
                const icons = el.querySelectorAll('svg, i, span');
                for (const icon of icons) {
                    const iconClass = (icon.className || "").toString().toLowerCase();
                    const iconRole = (icon.getAttribute("role") || "").toLowerCase();
                    if (
                        iconClass.includes("arrow") || iconClass.includes("chevron") || 
                        iconClass.includes("caret") || iconClass.includes("down") ||
                        iconClass.includes("dropdown") || iconRole === "presentation" ||
                        icon.tagName.toLowerCase() === "svg"
                    ) {
                        hasSvgOrIconChild = true;
                        break;
                    }
                }
                
                let hasSubmenuContainer = false;
                let sibling = el.nextElementSibling;
                while (sibling) {
                    const siblingClass = (sibling.className || "").toString().toLowerCase();
                    const siblingTag = sibling.tagName.toLowerCase();
                    if (siblingClass.includes("dropdown") || siblingClass.includes("menu") || 
                        siblingClass.includes("submenu") || siblingTag === "ul" || siblingTag === "ol") {
                        hasSubmenuContainer = true;
                        break;
                    }
                    sibling = sibling.nextElementSibling;
                }
                const parent = el.parentElement;
                if (parent) {
                    const menu = parent.querySelector('ul, [class*="menu"], [class*="dropdown"], [class*="submenu"]');
                    if (menu && menu !== el) {
                        hasSubmenuContainer = true;
                    }
                }
                
                const isDropdown = hasDropdownText ||
                                   hasArrowChar ||
                                   (hasDropdownClassOrId && (hasSvgOrIconChild || hasSubmenuContainer)) ||
                                   (el.getAttribute("aria-controls") && !el.getAttribute("aria-haspopup")) ||
                                   ((className.includes("nav") || className.includes("menu") || el.closest("nav") || el.closest("header")) && hasSvgOrIconChild);
                
                const isAriaRole = !!el.getAttribute("role");
                const tabindex = el.getAttribute("tabindex");
                
                let labelInNameMismatch = false;
                const visibleText = (el.innerText || "").trim();
                const visibleTextLower = visibleText.toLowerCase();
                const ariaLabel = (el.getAttribute("aria-label") || "").trim().toLowerCase();
                let ariaLabelledbyText = "";
                if (el.getAttribute("aria-labelledby")) {
                    const ids = el.getAttribute("aria-labelledby").split(/\\s+/);
                    ariaLabelledbyText = ids.map(id => {
                        const lbl = document.getElementById(id);
                        return lbl ? (lbl.innerText || lbl.textContent || "") : "";
                    }).filter(Boolean).join(" ").trim().toLowerCase();
                }
                const nameSource = ariaLabel || ariaLabelledbyText;
                if (nameSource && visibleTextLower && !nameSource.includes(visibleTextLower)) {
                    labelInNameMismatch = true;
                }

                return {
                    announcement: announcement.trim(),
                    role: role || "unknown",
                    name: name,
                    tagName: tagName,
                    id: el.id,
                    html: el.outerHTML.substring(0, 300),
                    isDropdown: isDropdown,
                    aria_haspopup: el.getAttribute("aria-haspopup"),
                    aria_expanded: el.getAttribute("aria-expanded"),
                    isAriaRole: isAriaRole,
                    tabindex: tabindex,
                    labelInNameMismatch: labelInNameMismatch,
                    visibleText: visibleText
                };
            }

            return elements.map(el => getAnnouncement(el));
        }"""
        
        computed_announcements = await page.evaluate(js_announcement_script)
        
        violations = []
        passes = []
        
        nvda_active = self.nvda.is_running()
        if nvda_active:
            logger.info("NVDA process is active on system. Speech integration enabled.")
            
        for item in computed_announcements:
            announcement = item["announcement"]
            role = item["role"]
            name = item["name"]
            html = item["html"]
            tagName = item["tagName"]
            element_id = item["id"]
            
            # Speak the announcement live if NVDA is running
            if nvda_active and announcement:
                self.nvda.speak(announcement)
                
            # Validation 1: Missing accessible label/name
            if not name:
                violations.append(Violation(
                    id="screen-reader-missing-label",
                    impact="serious",
                    description=f"Interactive element <{tagName}> is missing an accessible label for screen readers.",
                    help="Ensure all interactive elements have a descriptive accessible name (e.g. inner text, aria-label, or associated label).",
                    helpUrl="https://www.w3.org/WAI/WCAG22/Techniques/aria/ARIA14",
                    nodes=[{
                        "html": html,
                        "target": [f"{tagName}{'#' + element_id if element_id else ''}"]
                    }],
                    metadata={
                        "friendly_name": "Unlabeled Interactive Control - Screen Reader Accessible Name Missing",
                        "wcag_criteria": "4.1.2 Name, Role, Value",
                        "wcag_level": "A",
                        "severity": "Serious",
                        "business_impact": "Screen reader users will only hear 'button' or 'link' with no context about what the element does.",
                        "expected_result": "Interactive elements (like `<button>`, `<a>`, or `<input>`) MUST have a programmatically determinable text label (accessible name) so that screen readers can announce their purpose and role. It should announce: '[Purpose], [Role]', e.g. 'Submit Form, button'.",
                        "actual_result": "The element has no accessible name or label. Under screen reader emulation, the element is announced only by its generic role (e.g. 'button' or 'link') without any context, leaving users unable to identify its purpose.",
                        "steps_to_reproduce": "1. Open the page in a browser.\n2. Locate the targeted interactive element in the DOM or on screen.\n3. Navigate to the element using a screen reader or inspect its properties in the browser's Accessibility developer pane.\n4. Observe that the computed accessible name field is empty and screen reader announcement lacks descriptive context.",
                        "remediation": "Add inner text, an aria-label, or link the input to a label element using the 'for' attribute.",
                        "refined_by": "ScreenReaderSkill"
                    }
                ))
            # Validation 2: Vague/Confusing announcements
            elif name.lower() in ["click here", "read more", "more", "button", "link", "submit", "go"]:
                violations.append(Violation(
                    id="screen-reader-vague-label",
                    impact="moderate",
                    description=f"Interactive element <{tagName}> has a non-descriptive screen reader label: '{name}'.",
                    help="Provide screen reader labels that describe the element's specific purpose out of context.",
                    helpUrl="https://www.w3.org/WAI/WCAG22/Techniques/general/G91",
                    nodes=[{
                        "html": html,
                        "target": [f"{tagName}{'#' + element_id if element_id else ''}"]
                    }],
                    metadata={
                        "friendly_name": "Non-Descriptive Announcement - Vague or Ambiguous Screen Reader Label",
                        "wcag_criteria": "2.4.4 Link Purpose (In Context)",
                        "wcag_level": "A",
                        "severity": "Medium",
                        "business_impact": "Users tabbing through links/buttons out of context will hear generic announcements like 'click here link', making navigation slow and confusing.",
                        "expected_result": "Interactive element labels MUST convey their specific purpose out of context. For example, a read-more link should state what topic is being expanded (e.g. 'Read more about our services link' instead of 'Read more link').",
                        "actual_result": f"The element's accessible name is vague and generic ('{name}'). When read by a screen reader out of context, it announces '{announcement}', which fails to communicate the destination or target of the control.",
                        "steps_to_reproduce": f"1. Open the page in a browser.\n2. Locate the element labeled '{name}'.\n3. Use keyboard navigation to Tab to the element or read it with a screen reader active.\n4. Observe that the computed announcement is generic ('{announcement}') and does not describe the specific action or link destination.",
                        "remediation": "Update the element text or add an 'aria-label' with more context.",
                        "refined_by": "ScreenReaderSkill"
                    }
                ))
            else:
                passes.append({
                    "id": "screen-reader-pass",
                    "help": f"Accessible name verified on <{tagName}>",
                    "description": f"Screen reader announcement computed successfully: '{announcement}'",
                    "helpUrl": "https://www.w3.org/WAI/WCAG22/Understanding/name-role-value",
                    "tags": ["wcag2a", "wcag412"],
                    "metadata": {
                        "wcag_criteria": "4.1.2 Name, Role, Value",
                        "wcag_level": "A",
                        "severity": "Serious",
                        "expected_result": "Interactive elements must have a descriptive accessible name that a screen reader can compute and announce.",
                        "actual_result": f"Verification passed: Screen reader announcement computed successfully as '{announcement}'.",
                        "steps_to_reproduce": (
                            f"1. Locate the <{tagName}> element.\n"
                            f"2. Inspect its accessible name in the accessibility tree.\n"
                            f"3. Verify the computed announcement is: '{announcement}'."
                        ),
                        "remediation": "No remediation required. The accessible name complies with screen reader accessibility requirements.",
                        "business_impact": "Ensures screen reader users hear accurate and helpful context when interacting with elements."
                    }
                })

            # Validation 3: Dropdown Toggle Attributes
            is_dropdown = item.get("isDropdown")
            aria_haspopup = item.get("aria_haspopup")
            aria_expanded = item.get("aria_expanded")
            if is_dropdown and (not aria_haspopup or not aria_expanded):
                violations.append(Violation(
                    id="screen-reader-missing-dropdown-attributes",
                    impact="serious",
                    description=f"Dropdown toggle button <{tagName}> is missing 'aria-haspopup' or 'aria-expanded' attributes.",
                    help="Ensure dropdown toggle buttons have 'aria-haspopup=\"true\"' (or 'menu') and dynamically update 'aria-expanded=\"true/false\"'.",
                    helpUrl="https://www.w3.org/WAI/ARIA/apg/patterns/menu-button/",
                    nodes=[{"html": html, "target": [f"{tagName}{'#' + element_id if element_id else ''}"]}],
                    metadata={
                        "friendly_name": "Dropdown Menu Toggle Missing ARIA Attributes",
                        "wcag_criteria": "4.1.2 Name, Role, Value",
                        "wcag_level": "A",
                        "severity": "Serious",
                        "business_impact": "Screen reader users will not know that this button toggles a menu/dropdown, nor whether the dropdown is currently expanded or collapsed.",
                        "expected_result": "Dropdown toggle buttons MUST have 'aria-haspopup=\"true\"' (or 'menu') and 'aria-expanded=\"true/false\"' to indicate their menu behavior and current state.",
                        "actual_result": f"Dropdown button has aria-haspopup={aria_haspopup} and aria-expanded={aria_expanded}.",
                        "steps_to_reproduce": "1. Inspect the dropdown toggle button.\n2. Verify if 'aria-haspopup' or 'aria-expanded' attributes are present and correct.",
                        "remediation": "Add aria-haspopup=\"true\" and aria-expanded=\"false\" attributes to the trigger element, and update aria-expanded dynamically on activation.",
                        "refined_by": "ScreenReaderSkill"
                    }
                ))

            # Validation 4: Focusable Tabindex on Custom ARIA Roles
            is_custom_role = item.get("isAriaRole")
            tabindex = item.get("tabindex")
            if is_custom_role and tagName not in ["button", "a", "input", "select", "textarea"] and (tabindex is None or int(tabindex) < 0):
                violations.append(Violation(
                    id="screen-reader-aria-role-missing-handlers",
                    impact="serious",
                    description=f"Element <{tagName}> with role='{role}' is missing a valid 'tabindex' attribute for keyboard focusability.",
                    help="Interactive elements with custom ARIA roles must have tabindex='0' to be accessible in the keyboard tab order.",
                    helpUrl="https://www.w3.org/WAI/ARIA/apg/practices/keyboard-interface/",
                    nodes=[{"html": html, "target": [f"{tagName}{'#' + element_id if element_id else ''}"]}],
                    metadata={
                        "friendly_name": "ARIA Control Not Keyboard Focusable",
                        "wcag_criteria": "2.1.1 Keyboard",
                        "wcag_level": "A",
                        "severity": "Serious",
                        "business_impact": "Keyboard-only and screen reader users cannot focus or interact with this custom control.",
                        "expected_result": "Interactive elements with custom ARIA roles MUST have tabindex='0' to ensure they receive keyboard focus.",
                        "actual_result": f"Element has role='{role}' but has tabindex={tabindex}.",
                        "steps_to_reproduce": f"1. Navigate the page using the Tab key.\n2. Observe that the element with role='{role}' is skipped.",
                        "remediation": "Add tabindex=\"0\" to the element to make it focusable.",
                        "refined_by": "ScreenReaderSkill"
                    }
                ))

            # Validation 5: WCAG 2.5.3 Label in Name
            label_mismatch = item.get("labelInNameMismatch")
            visible_text = item.get("visibleText")
            if label_mismatch:
                violations.append(Violation(
                    id="screen-reader-label-in-name-mismatch",
                    impact="moderate",
                    description=f"Accessible name for <{tagName}> does not contain its visible text '{visible_text}'.",
                    help="Ensure that the accessible name (aria-label/aria-labelledby) contains the visible text label.",
                    helpUrl="https://www.w3.org/WAI/WCAG22/Understanding/label-in-name.html",
                    nodes=[{"html": html, "target": [f"{tagName}{'#' + element_id if element_id else ''}"]}],
                    metadata={
                        "friendly_name": "Label in Name Mismatch",
                        "wcag_criteria": "2.5.3 Label in Name",
                        "wcag_level": "A",
                        "severity": "Medium",
                        "business_impact": "Speech-input users who say the visible label will fail to activate the button, and screen reader users will experience a disconnect between visual and spoken UI labels.",
                        "expected_result": "The programmatic accessible name (e.g. from aria-label) MUST contain the visible text label of the control.",
                        "actual_result": f"Visible text is '{visible_text}' but the computed accessible name is '{name}'.",
                        "steps_to_reproduce": "1. Inspect the element's visible text and its 'aria-label' or 'aria-labelledby' attributes.\n2. Observe that the visible text is not included in the accessible name.",
                        "remediation": "Update the aria-label to include the exact visible text content of the element as a prefix or substring.",
                        "refined_by": "ScreenReaderSkill"
                    }
                ))

        # --- GLOBAL LANDMARKS AND HEADINGS VALIDATION ---
        
        js_landmarks_script = """() => {
            const navs = Array.from(document.querySelectorAll('nav, [role="navigation"]'));
            const mainCount = document.querySelectorAll('main, [role="main"]').length;
            
            const unlabeledNavs = [];
            if (navs.length > 1) {
                navs.forEach((nav, idx) => {
                    const label = nav.getAttribute('aria-label') || nav.getAttribute('aria-labelledby');
                    if (!label) {
                        unlabeledNavs.push({
                            html: nav.outerHTML.substring(0, 300),
                            id: nav.id,
                            tagName: nav.tagName.toLowerCase()
                        });
                    }
                });
            }
            
            const headingElements = Array.from(document.querySelectorAll('h1, h2, h3, h4, h5, h6, [role="heading"]'));
            const headings = headingElements.map(h => {
                let level = parseInt(h.tagName.substring(1));
                if (isNaN(level)) {
                    level = parseInt(h.getAttribute('aria-level') || '2');
                }
                return {
                    level: level,
                    html: h.outerHTML.substring(0, 300),
                    tagName: h.tagName.toLowerCase(),
                    id: h.id
                };
            });
            
            return {
                mainCount,
                unlabeledNavs,
                headings
            };
        }"""
        
        try:
            landmark_data = await page.evaluate(js_landmarks_script)
            
            # 1. Main Landmark check
            main_count = landmark_data.get("mainCount", 0)
            if main_count == 0:
                violations.append(Violation(
                    id="screen-reader-missing-landmarks",
                    impact="moderate",
                    description="The page is missing a main landmark (<main> or role='main').",
                    help="Wrap the primary content of the page in a <main> element or apply role='main'.",
                    helpUrl="https://www.w3.org/WAI/WCAG22/Techniques/aria/ARIA11",
                    nodes=[{"html": "<body>", "target": ["body"]}],
                    metadata={
                        "friendly_name": "Main Landmark Missing",
                        "wcag_criteria": "1.3.1 Info and Relationships",
                        "wcag_level": "A",
                        "severity": "Medium",
                        "business_impact": "Screen reader users cannot easily jump to the primary content of the page using landmark navigation shortcuts.",
                        "expected_result": "The page MUST contain exactly one main landmark element (<main> or role='main') representing the unique content of the page.",
                        "actual_result": "No main landmark was found on the page.",
                        "steps_to_reproduce": "1. Inspect the page's HTML structure.\n2. Confirm that there is no <main> element or element with role='main'.",
                        "remediation": "Wrap the main content area of the page in a <main> tag.",
                        "refined_by": "ScreenReaderSkill"
                    }
                ))
                
            # 2. Unlabeled Navigation Landmark check
            unlabeled_navs = landmark_data.get("unlabeledNavs", [])
            for nav in unlabeled_navs:
                violations.append(Violation(
                    id="screen-reader-missing-landmarks",
                    impact="minor",
                    description="Multiple navigation landmarks exist but are not labeled.",
                    help="Provide a unique aria-label or aria-labelledby on each navigation landmark to distinguish them.",
                    helpUrl="https://www.w3.org/WAI/WCAG22/Techniques/aria/ARIA6",
                    nodes=[{"html": nav["html"], "target": [f"{nav['tagName']}{'#' + nav['id'] if nav['id'] else ''}"]}],
                    metadata={
                        "friendly_name": "Unlabeled Navigation Landmark",
                        "wcag_criteria": "1.3.1 Info and Relationships",
                        "wcag_level": "A",
                        "severity": "Minor",
                        "business_impact": "Screen reader users will hear multiple 'navigation' areas but won't know which is the main menu, sidebar navigation, or footer navigation.",
                        "expected_result": "If multiple `<nav>` or navigation landmarks exist on a page, they must have unique accessible names (aria-label) to distinguish them.",
                        "actual_result": f"Found unlabeled navigation landmark: {nav['html']}.",
                        "steps_to_reproduce": "1. Locate the navigation landmarks on the page.\n2. Verify if they contain 'aria-label' or 'aria-labelledby'.",
                        "remediation": "Add a unique aria-label to the <nav> element (e.g. aria-label=\"Main Navigation\").",
                        "refined_by": "ScreenReaderSkill"
                    }
                ))
                
            # 3. Headings structure check
            headings = landmark_data.get("headings", [])
            has_h1 = any(h["level"] == 1 for h in headings)
            if headings and not has_h1:
                violations.append(Violation(
                    id="screen-reader-broken-headings",
                    impact="moderate",
                    description="The page is missing a Level 1 Heading (h1).",
                    help="Ensure the page has a single, descriptive <h1> heading marking the main topic.",
                    helpUrl="https://www.w3.org/WAI/WCAG22/Techniques/general/G141",
                    nodes=[{"html": headings[0]["html"] if headings else "<body>", "target": [headings[0]["tagName"] if headings else "body"]}],
                    metadata={
                        "friendly_name": "Level 1 Heading (H1) Missing",
                        "wcag_criteria": "1.3.1 Info and Relationships",
                        "wcag_level": "A",
                        "severity": "Medium",
                        "business_impact": "Screen reader users use <h1> to confirm they have landed on the correct page and understand its main purpose.",
                        "expected_result": "The page should have a clear, descriptive <h1> heading.",
                        "actual_result": "No <h1> heading was found on the page.",
                        "steps_to_reproduce": "1. Inspect the headings of the page.\n2. Observe that there is no <h1> heading element.",
                        "remediation": "Add an <h1> heading at the beginning of the main content.",
                        "refined_by": "ScreenReaderSkill"
                    }
                ))
                
            prev_level = None
            prev_tagName = None
            for h in headings:
                level = h["level"]
                if prev_level and level > prev_level + 1:
                    violations.append(Violation(
                        id="screen-reader-broken-headings",
                        impact="minor",
                        description=f"Skipped heading level: <{h['tagName']}> follows <{prev_tagName}>.",
                        help="Ensure heading levels are structured sequentially (e.g., h1 followed by h2, h2 followed by h3).",
                        helpUrl="https://www.w3.org/WAI/WCAG22/Techniques/general/G141",
                        nodes=[{"html": h["html"], "target": [f"{h['tagName']}{'#' + h['id'] if h['id'] else ''}"]}],
                        metadata={
                            "friendly_name": "Skipped Heading Level",
                            "wcag_criteria": "1.3.1 Info and Relationships",
                            "wcag_level": "A",
                            "severity": "Minor",
                            "business_impact": "Screen reader users rely on a logical, sequential heading structure to build a mental map of the content layout. Skipped levels break this outline.",
                            "expected_result": "Heading levels MUST increase sequentially by only one level at a time (e.g. h2 can be followed by h3, but h2 cannot skip to h4).",
                            "actual_result": f"Heading level skipped from h{prev_level} to h{level} at element: {h['html']}.",
                            "steps_to_reproduce": "1. Scan headings sequentially.\n2. Observe skipped heading levels.",
                            "remediation": "Change the heading tag level to follow the logical sequential hierarchy (e.g., h3 instead of h4).",
                            "refined_by": "ScreenReaderSkill"
                        }
                    ))
                prev_level = level
                prev_tagName = h["tagName"]
                
        except Exception as landmark_err:
            logger.error(f"Failed in global landmark or heading validation: {landmark_err}")
            
        return {
            "violations": violations,
            "passes": passes
        }

screen_reader_skill = ScreenReaderSkill()
