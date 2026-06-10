from playwright.async_api import Page
from common.schemas.audit import Violation
import logging

logger = logging.getLogger(__name__)

class KeyboardNavSkill:
    """
    Skill for testing keyboard navigation, focus visibility, logical focus order,
    and detecting keyboard traps.
    """
    
    async def run_keyboard_test(self, page: Page) -> dict:
        logger.info("Running Keyboard Navigation accessibility checks")
        
        # 1. Reset focus to the top of the page
        try:
            await page.focus("body")
        except Exception as e:
            logger.debug(f"Failed to focus body: {e}")

        # Scan for non-focusable interactive elements
        try:
            non_focusable_interactive = await page.evaluate("""() => {
                const candidates = Array.from(document.querySelectorAll(
                    'div[role="button"], span[role="button"], div[role="link"], span[role="link"], [role="menuitem"], [role="tab"], [role="checkbox"], [role="radio"]'
                ));
                return candidates.filter(el => {
                    const tabindex = el.getAttribute("tabindex");
                    // If no tabindex is set, or if it is negative (excluded from tab flow)
                    const isExcluded = tabindex === null || parseInt(tabindex) < 0;
                    
                    const rect = el.getBoundingClientRect();
                    const isVisible = rect.width > 0 && rect.height > 0 && window.getComputedStyle(el).display !== 'none';
                    
                    return isExcluded && isVisible;
                }).map(el => ({
                    tagName: el.tagName.toLowerCase(),
                    id: el.id,
                    html: el.outerHTML.substring(0, 300),
                    role: el.getAttribute("role")
                }));
            }""")
            for item in non_focusable_interactive:
                violations.append(Violation(
                    id="keyboard-non-focusable-interactive",
                    impact="serious",
                    description=f"Interactive control <{item['tagName']}> with role='{item['role']}' cannot be focused via keyboard.",
                    help="Add tabindex='0' to ensure keyboard-only and screen reader users can navigate to this element.",
                    helpUrl="https://www.w3.org/WAI/ARIA/apg/practices/keyboard-interface/",
                    nodes=[{"html": item["html"], "target": [f"{item['tagName']}{'#' + item['id'] if item['id'] else ''}"]}],
                    metadata={
                        "friendly_name": "Interactive Control Excluded from Tab Order",
                        "wcag_criteria": "2.1.1 Keyboard",
                        "wcag_level": "A",
                        "severity": "Serious",
                        "business_impact": "Keyboard-only and assistive technology users will not be able to navigate to, focus on, or interact with this custom control.",
                        "expected_result": "Any element with an interactive ARIA role MUST be focusable (e.g. have tabindex='0' or be a semantic button/link).",
                        "actual_result": f"Element has role='{item['role']}' but lacks a tab index, making it unreachable via keyboard.",
                        "steps_to_reproduce": "1. Scan the page using keyboard navigation.\n2. Observe that this interactive control is skipped.",
                        "remediation": "Add tabindex=\"0\" to the element.",
                        "refined_by": "KeyboardNavSkill"
                    }
                ))
        except Exception as e:
            logger.error(f"Failed to scan non-focusable interactive controls: {e}")

        # 1. Reset focus to the top of the page
        try:
            await page.focus("body")
        except Exception as e:
            logger.debug(f"Failed to focus body: {e}")

        # We tab through elements and record their properties
        active_elements = []
        max_tabs = 50  # Prevent infinite loop
        violations = []
        passes = []

        previous_rect = None
        previous_active = None

        for i in range(max_tabs):
            await page.keyboard.press("Tab")
            await page.wait_for_timeout(100)  # Brief wait for focus styles to apply
            
            # Extract info about the currently active element
            active_info = await page.evaluate("""() => {
                const el = document.activeElement;
                if (!el || el === document.body || el === document.documentElement) {
                    return null;
                }
                
                // Get style difference between focused and blurred state
                const styleFocused = { ...window.getComputedStyle(el) };
                el.blur();
                const styleBlurred = { ...window.getComputedStyle(el) };
                el.focus();
                
                const rect = el.getBoundingClientRect();
                
                // Check if element is visually hidden or size is 0 or off-screen
                const isVisuallyHidden = styleFocused.opacity === '0' || 
                                         styleFocused.visibility === 'hidden' || 
                                         rect.width === 0 || rect.height === 0 ||
                                         rect.x < -200 || rect.y < -200;
                
                // Outline/border/shadow checks for visible focus indicator
                const hasVisibleOutline = styleFocused.outlineStyle !== 'none' && parseInt(styleFocused.outlineWidth) > 0;
                const outlineChanged = styleFocused.outlineStyle !== styleBlurred.outlineStyle || 
                                       styleFocused.outlineWidth !== styleBlurred.outlineWidth || 
                                       styleFocused.outlineColor !== styleBlurred.outlineColor;
                const borderChanged = styleFocused.borderColor !== styleBlurred.borderColor;
                const shadowChanged = styleFocused.boxShadow !== styleBlurred.boxShadow && styleFocused.boxShadow !== 'none';
                const bgChanged = styleFocused.backgroundColor !== styleBlurred.backgroundColor;
                const colorChanged = styleFocused.color !== styleBlurred.color;
                
                const focusVisible = hasVisibleOutline || outlineChanged || borderChanged || shadowChanged || bgChanged || colorChanged;
                
                const className = (el.className || "").toString().toLowerCase();
                const textLower = (el.innerText || el.getAttribute('aria-label') || "").toLowerCase();
                const isDropdown = className.includes("dropdown") ||
                                   className.includes("menu-toggle") ||
                                   className.includes("has-submenu") ||
                                   textLower.includes("▼") ||
                                   textLower.includes("▾") ||
                                   textLower.includes("dropdown") ||
                                   textLower.includes("menu") ||
                                   (el.getAttribute("aria-controls") && !el.getAttribute("aria-haspopup"));

                return {
                    tagName: el.tagName.toLowerCase(),
                    id: el.id,
                    className: el.className,
                    text: (el.innerText || el.getAttribute('aria-label') || el.getAttribute('placeholder') || '').trim(),
                    html: el.outerHTML.substring(0, 300),
                    isVisuallyHidden: isVisuallyHidden,
                    focusVisible: focusVisible,
                    rect: {
                        x: rect.x,
                        y: rect.y,
                        width: rect.width,
                        height: rect.height
                    },
                    role: el.getAttribute('role') || '',
                    aria_haspopup: el.getAttribute('aria-haspopup'),
                    aria_expanded: el.getAttribute('aria-expanded'),
                    href: el.getAttribute('href') || '',
                    isDropdown: isDropdown
                };
            }""")

            if not active_info:
                # Reached end of document tab cycle or tabbed out of viewport
                break

            # Verification 3: Detect Keyboard Trap (Check before loop/visit check)
            if previous_active and active_info["html"] == previous_active["html"]:
                violations.append(Violation(
                    id="keyboard-trap",
                    impact="critical",
                    description=f"Keyboard navigation is trapped on <{active_info['tagName']}>. Focus cannot advance.",
                    help="Ensure keyboard users can navigate past all elements using the Tab key.",
                    helpUrl="https://www.w3.org/WAI/WCAG22/Techniques/general/G21",
                    nodes=[{
                        "html": active_info["html"],
                        "target": [f"{active_info['tagName']}{'#' + active_info['id'] if active_info['id'] else ''}"]
                    }],
                    metadata={
                        "friendly_name": "Keyboard Navigation Blocked - Focus Trap Detected",
                        "wcag_criteria": "2.1.2 No Keyboard Trap",
                        "wcag_level": "A",
                        "severity": "Critical",
                        "business_impact": "Keyboard-only and screen reader users will be completely unable to read or interact with any content past this point.",
                        "expected_result": "Keyboard focus MUST be able to leave interactive elements (like input fields, frames, or dialogs) using standard keyboard navigation keys (e.g. Tab/Shift+Tab). The user must be able to navigate to other interactive controls.",
                        "actual_result": "Keyboard focus is trapped inside the element. Pressing Tab does not advance the focus to the next element, making it impossible to navigate further.",
                        "steps_to_reproduce": "1. Open the page in a browser.\n2. Navigate sequentially using the Tab key until focus reaches the targeted element.\n3. Press the Tab key again.\n4. Observe that the focus remains trapped within the element and cannot be advanced to other controls.",
                        "remediation": "Ensure keydown events do not trap focus on this element. Do not prevent default Tab behavior unless managing focus within a modal dialog.",
                        "refined_by": "KeyboardNavSkill"
                    }
                ))
                break

            # Check for loops (visited element)
            if any(info["html"] == active_info["html"] for info in active_elements):
                break

            active_elements.append(active_info)

            # Verification 1: Skip Link Check on first focused element
            if len(active_elements) == 1:
                text_lower = active_info["text"].lower()
                href_lower = active_info["href"].lower()
                id_lower = active_info["id"].lower()
                is_skip = "skip" in text_lower or "skip" in href_lower or "skip" in id_lower or "bypass" in text_lower
                if not is_skip:
                    violations.append(Violation(
                        id="keyboard-skip-link-missing",
                        impact="moderate",
                        description=f"First focused element on page <{active_info['tagName']}> is not a skip link.",
                        help="Add a visible 'Skip to Main Content' link as the very first focusable element on the page.",
                        helpUrl="https://www.w3.org/WAI/WCAG22/Techniques/general/G1",
                        nodes=[{"html": active_info["html"], "target": [f"{active_info['tagName']}{'#' + active_info['id'] if active_info['id'] else ''}"]}],
                        metadata={
                            "friendly_name": "Skip Link Missing or Not First",
                            "wcag_criteria": "2.4.1 Bypass Blocks",
                            "wcag_level": "A",
                            "severity": "Medium",
                            "business_impact": "Keyboard-only users must tab through all header links, navigation menus, and search boxes on every page load before reaching the main content.",
                            "expected_result": "The first focusable element on the page MUST be a 'Skip to Content' link that jumps keyboard focus directly to the main content container.",
                            "actual_result": f"The first focusable element is <{active_info['tagName']}> with text '{active_info['text']}'.",
                            "steps_to_reproduce": "1. Refresh the page.\n2. Press the Tab key once.\n3. Observe if focus is set on a bypass / skip link.",
                            "remediation": "Insert a <a href=\"#main\">Skip to Content</a> link at the very top of the <body>.",
                            "refined_by": "KeyboardNavSkill"
                        }
                    ))

            # Verification 2: Hidden Focusable element
            if active_info["isVisuallyHidden"]:
                violations.append(Violation(
                    id="keyboard-hidden-focusable",
                    impact="serious",
                    description=f"Visually hidden element <{active_info['tagName']}> receives keyboard focus.",
                    help="Set tabindex='-1', display: none, or visibility: hidden on elements that are hidden from sighted users.",
                    helpUrl="https://www.w3.org/WAI/WCAG22/Understanding/focus-order.html",
                    nodes=[{"html": active_info["html"], "target": [f"{active_info['tagName']}{'#' + active_info['id'] if active_info['id'] else ''}"]}],
                    metadata={
                        "friendly_name": "Focusable Element is Visually Hidden",
                        "wcag_criteria": "2.4.3 Focus Order",
                        "wcag_level": "A",
                        "severity": "Serious",
                        "business_impact": "Sighted keyboard-only users will experience their focus disappearing into blank sections of the page, leading to disorientation.",
                        "expected_result": "Visually hidden elements MUST NOT receive keyboard focus. They must be removed from the tab order using tabindex='-1' or CSS visibility:hidden / display:none.",
                        "actual_result": f"Element is visually hidden (opacity/size/coordinates hidden) but receives focus.",
                        "steps_to_reproduce": "1. Tab sequentially through the page.\n2. Observe that focus disappears or lands on an invisible control.",
                        "remediation": "Apply display: none or visibility: hidden to the element, or add tabindex=\"-1\".",
                        "refined_by": "KeyboardNavSkill"
                    }
                ))

            # Verification 4: Verify Focus Visibility
            if not active_info["focusVisible"]:
                violations.append(Violation(
                    id="focus-invisible",
                    impact="serious",
                    description=f"Interactive element <{active_info['tagName']}> does not have a visible focus indicator.",
                    help="Provide a clear, visible focus outline or visual change when elements receive keyboard focus.",
                    helpUrl="https://www.w3.org/WAI/WCAG22/Techniques/css/C15",
                    nodes=[{
                        "html": active_info["html"],
                        "target": [f"{active_info['tagName']}{'#' + active_info['id'] if active_info['id'] else ''}"]
                    }],
                    metadata={
                        "friendly_name": "Keyboard Focus Indicator Missing - Inactive Focus Outline",
                        "wcag_criteria": "2.4.7 Focus Visible",
                        "wcag_level": "AA",
                        "severity": "Serious",
                        "business_impact": "Sighted keyboard-only users will not know which element is currently active, making navigation guesswork.",
                        "expected_result": "Interactive elements MUST display a highly visible focus indicator (e.g. a high-contrast focus ring, border outline, or background change) when focused via keyboard to signify their active state.",
                        "actual_result": "No visible focus indicator or style change is rendered when the element receives focus, leaving sighted keyboard users without any visual cue of their current page position.",
                        "steps_to_reproduce": "1. Open the page in a browser.\n2. Press the Tab key repeatedly to navigate to the targeted interactive element.\n3. Observe that the element shows no high-contrast visual outline, outline ring, or background color shift upon receiving focus.",
                        "remediation": "Add a CSS :focus or :focus-visible style. Do not use 'outline: none' without providing an alternative high-contrast focus style.",
                        "refined_by": "KeyboardNavSkill"
                    }
                ))
            else:
                passes.append({
                    "id": "focus-visible",
                    "help": f"Focus indicator visible on <{active_info['tagName']}>",
                    "description": f"The interactive element <{active_info['tagName']}> has a visible focus indicator when active.",
                    "helpUrl": "https://www.w3.org/WAI/WCAG22/Understanding/focus-visible",
                    "tags": ["wcag2aa", "wcag247", "wcag22"],
                    "metadata": {
                        "wcag_criteria": "2.4.7 Focus Visible",
                        "wcag_level": "AA",
                        "severity": "Serious",
                        "expected_result": "Interactive elements should receive a clear, visible focus outline or visual change when they receive keyboard focus.",
                        "actual_result": f"Verification passed: <{active_info['tagName']}> has a visible focus indicator when focused.",
                        "steps_to_reproduce": "1. Navigate to the page.\n2. Use the Tab key to focus on the interactive element.\n3. Verify that a high-contrast visual outline or color shift is visible on the element.",
                        "remediation": "No remediation required. Focus style indicator is visible.",
                        "business_impact": "Provides critical visual feedback for keyboard-only users to see their current location on the page."
                    }
                })

            # Verification 5: Verify Logical Focus Order
            rect = active_info["rect"]
            if previous_rect:
                # If focus jumps up vertically by more than 150px
                if rect["y"] < previous_rect["y"] - 150:
                    violations.append(Violation(
                        id="focus-order-illogical",
                        impact="moderate",
                        description=f"Potential illogical focus jump from previous element to <{active_info['tagName']}>.",
                        help="Ensure keyboard focus order follows the visual and reading flow of the page.",
                        helpUrl="https://www.w3.org/WAI/WCAG22/Techniques/general/G59",
                        nodes=[{
                            "html": active_info["html"],
                            "target": [f"{active_info['tagName']}{'#' + active_info['id'] if active_info['id'] else ''}"]
                        }],
                        metadata={
                            "friendly_name": "Disorienting Navigation Path - Illogical Keyboard Focus Order",
                            "wcag_criteria": "2.4.3 Focus Order",
                            "wcag_level": "A",
                            "severity": "Medium",
                            "business_impact": "Keyboard users may find the navigation order disorienting as the focus jumps unexpectedly across different sections of the page.",
                            "expected_result": "The keyboard focus path MUST follow a logical sequence (top-to-bottom, left-to-right) matching the visual reading layout of the page.",
                            "actual_result": f"The focus order jumps unexpectedly. Upon pressing Tab, the focus moved vertically upwards from y={previous_rect['y']} to y={rect['y']} rather than following the standard reading sequence.",
                            "steps_to_reproduce": "1. Open the page in a browser.\n2. Use the Tab key to navigate sequentially through page elements.\n3. Observe the sequential path of focus indicators on the screen.\n4. Verify that focus jumps unexpectedly out of standard visual sequence (e.g., jumping back up the page).",
                            "remediation": "Ensure elements are placed in the DOM in their logical reading order. Avoid using positive tabindex values.",
                            "refined_by": "KeyboardNavSkill"
                        }
                    ))
                else:
                    passes.append({
                        "id": "focus-order",
                        "help": f"Logical focus progression to <{active_info['tagName']}>",
                        "description": f"Focus transitioned to <{active_info['tagName']}> in a logical vertical sequence.",
                        "helpUrl": "https://www.w3.org/WAI/WCAG22/Understanding/focus-order",
                        "tags": ["wcag2a", "wcag243"],
                        "metadata": {
                            "wcag_criteria": "2.4.3 Focus Order",
                            "wcag_level": "A",
                            "severity": "Moderate",
                            "expected_result": "Keyboard focus order should follow the visual and logical reading flow of the page.",
                            "actual_result": f"Verification passed: Focus transitioned to <{active_info['tagName']}> in a logical vertical sequence.",
                            "steps_to_reproduce": "1. Tab sequentially through elements on the page.\n2. Observe the focus path.\n3. Verify that focus moves in a logical order (top-to-bottom, left-to-right) corresponding to the visual flow.",
                            "remediation": "No remediation required. Keyboard navigation order is logical.",
                            "business_impact": "Prevents keyboard navigation from jumping randomly, which confuses and disorients users."
                        }
                    })

            previous_rect = rect
            previous_active = active_info

        # Test Dropdown Interactions and Keyboard Menu patterns
        # Look for the first dropdown button we found during tabbing
        dropdown_triggers = [el for el in active_elements if el.get("isDropdown") or el.get("aria_haspopup")]
        if dropdown_triggers:
            target_trigger = dropdown_triggers[0]
            logger.info(f"[KB-NAV] Testing interactive keyboard pattern on dropdown trigger: {target_trigger['html']}")
            try:
                # 1. Focus the dropdown trigger again
                selector = f"{target_trigger['tagName']}"
                if target_trigger["id"]:
                    selector += f"#{target_trigger['id']}"
                elif target_trigger["className"]:
                    # Clean class names for CSS selector
                    first_class = target_trigger["className"].split()[0]
                    selector += f".{first_class}"
                    
                locator = page.locator(selector).first
                if await locator.count() > 0:
                    await locator.focus()
                    
                    # 2. Press Enter to open
                    await page.keyboard.press("Enter")
                    await page.wait_for_timeout(200)
                    
                    # 3. Check if focus moved to dropdown item
                    focused_tag = await page.evaluate("document.activeElement.tagName.toLowerCase()")
                    focused_text = await page.evaluate("document.activeElement.innerText || ''")
                    
                    # Try navigating with down arrow key
                    await page.keyboard.press("ArrowDown")
                    await page.wait_for_timeout(100)
                    new_focused_text = await page.evaluate("document.activeElement.innerText || ''")
                    
                    # If pressing Down Arrow or Enter did not change the focused element text or role
                    # (signifying arrow key menu navigation does not work), raise warning/violation
                    if focused_text == new_focused_text:
                        violations.append(Violation(
                            id="keyboard-dropdown-navigation-failure",
                            impact="serious",
                            description=f"Dropdown menu items triggered by <{target_trigger['tagName']}> cannot be navigated using Arrow keys.",
                            help="Implement keyboard navigation for menus using ArrowDown/ArrowUp, and enable Escape to close the menu.",
                            helpUrl="https://www.w3.org/WAI/ARIA/apg/patterns/menu-button/",
                            nodes=[{"html": target_trigger["html"], "target": [selector]}],
                            metadata={
                                "friendly_name": "Dropdown Keyboard Widget Pattern Failure",
                                "wcag_criteria": "2.1.1 Keyboard",
                                "wcag_level": "A",
                                "severity": "Serious",
                                "business_impact": "Keyboard users will have to tab through every dropdown submenu item to advance, or will be unable to open/navigate the dropdown submenus entirely.",
                                "expected_result": "Dropdown menus MUST support standard keyboard interaction patterns: Space/Enter opens the menu, ArrowDown/ArrowUp navigates through items, and Escape closes the menu.",
                                "actual_result": "Menu opened but Arrow keys do not navigate the items, or the focus remained static.",
                                "steps_to_reproduce": f"1. Focus on the dropdown trigger '{target_trigger['text']}'.\n2. Press Enter to open the menu.\n3. Press ArrowDown key repeatedly.\n4. Observe that the focus does not move to menu items.",
                                "remediation": "Add keyboard keydown listeners on the menu container to capture ArrowDown, ArrowUp, and Escape keys, and programmatically adjust focus.",
                                "refined_by": "KeyboardNavSkill"
                            }
                        ))
                    
                    # 4. Press Escape to close and check focus restoration
                    await page.keyboard.press("Escape")
                    await page.wait_for_timeout(200)
                    restored_tag = await page.evaluate("document.activeElement.tagName.toLowerCase()")
                    if restored_tag != target_trigger["tagName"]:
                        violations.append(Violation(
                            id="keyboard-dropdown-navigation-failure",
                            impact="moderate",
                            description=f"Closing the dropdown menu did not restore focus to the trigger button <{target_trigger['tagName']}>.",
                            help="Ensure that closing submenus, modals, or dialogs restores focus back to the triggering element.",
                            helpUrl="https://www.w3.org/WAI/ARIA/apg/practices/keyboard-interface/",
                            nodes=[{"html": target_trigger["html"], "target": [selector]}],
                            metadata={
                                "friendly_name": "Focus Restoration Failure",
                                "wcag_criteria": "2.4.3 Focus Order",
                                "wcag_level": "A",
                                "severity": "Medium",
                                "business_impact": "Keyboard users are thrown back to the top of the page or lost in the DOM after closing a menu, forced to tab through the whole page again.",
                                "expected_result": "Closing a menu, modal, or dialog trigger MUST restore focus back to the triggering element.",
                                "actual_result": f"Focus was left on <{restored_tag}> instead of returning to <{target_trigger['tagName']}>.",
                                "steps_to_reproduce": "1. Focus and activate the dropdown menu.\n2. Press Escape to close it.\n3. Verify if focus is returned to the trigger button.",
                                "remediation": "Programmatically focus the trigger element when the dropdown or modal is closed.",
                                "refined_by": "KeyboardNavSkill"
                            }
                        ))
            except Exception as e:
                logger.error(f"Failed dropdown keyboard pattern simulation: {e}")

        return {
            "violations": violations,
            "passes": passes
        }

keyboard_nav_skill = KeyboardNavSkill()
