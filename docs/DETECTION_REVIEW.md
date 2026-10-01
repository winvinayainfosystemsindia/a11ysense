# A11ySense AI — Detection Logic Review & False-Positive Mitigation

> **Note**: This document is a technical review and recommendation specification. In accordance with project requirements, detection logic in `keyboard_nav.py` and `screen_reader.py` has **not** been modified in this release; all improvements here are proposed for subsequent detection engine updates.

---

## Executive Summary
This document reviews five key areas where automated heuristics in `screen_reader.py` and `keyboard_nav.py` are prone to false positives or standard deviations. For each item, we provide the code reference, technical analysis, WCAG / WAI-ARIA standard context, and the recommended implementation.

---

## 1. Item A: `role="menuitem"` with `tabindex="-1"` (Roving Tabindex)

### Code Reference
- File: `backend/app/core/skills/implementations/screen_reader.py`
- Lines: ~530–547 (`Validation 4: ARIA role interactive tabindex validation`)

### Current Behavior
The scanner inspects elements with interactive ARIA roles (e.g., `button`, `menuitem`, `tab`, `link`). If `tabindex` is negative (`-1`) or missing, it triggers a `screen-reader-aria-role-missing-handlers` or focus failure violation stating:
> *"Interactive elements with custom ARIA roles MUST have tabindex='0' to ensure they receive keyboard focus."*

### Accessibility Standard (WAI-ARIA APG)
In the WAI-ARIA Authoring Practices Guide (APG) for **Menu**, **Menubar**, and **Tabs** patterns, the **Roving Tabindex** technique is the standard recommendation:
- Only the currently active menuitem or tab has `tabindex="0"`.
- All other menuitems or tabs **must** have `tabindex="-1"`.
- Navigation between items is performed using arrow keys (`Up`/`Down` or `Left`/`Right`), not the `Tab` key.
- Requiring all `menuitem` elements to have `tabindex="0"` breaks the roving tabindex pattern and floods the global Tab order.

### Proposed Improvement
```python
# Before flagging tabindex="-1", check if element is inside a composite widget
parent_role = item.get("parentRole")  # e.g., 'menu', 'menubar', 'tablist', 'grid'
if role in ("menuitem", "menuitemcheckbox", "menuitemradio") and parent_role in ("menu", "menubar"):
    # Exempt from tabindex="0" requirement if roving tabindex is managed
    pass
elif role == "tab" and parent_role == "tablist":
    # Exempt non-active tabs with tabindex="-1"
    pass
```

---

## 2. Item B: Label-in-Name Mismatch (`screen-reader-label-in-name-mismatch`)

### Code Reference
- File: `backend/app/core/skills/implementations/screen_reader.py`
- Lines: ~548–571 (`Validation 5: WCAG 2.5.3 Label in Name`)

### Current Behavior
The script compares visible element text (`visibleText`) with the computed accessible name (`name`). In earlier revisions, exact equality or strict prefix matching was checked, and non-standard severity `"Medium"` was assigned.

### Accessibility Standard (WCAG 2.5.3 Success Criterion)
> *"For user interface components with labels that include text or images of text, the name contains the text that is presented visually."*

Key requirements:
1. The accessible name must **contain** the visual text; it does not need to be an exact match. (e.g. Visible: `"Search"`, Name: `"Search our catalog"` is fully compliant).
2. Comparison must be case-insensitive and ignore leading/trailing whitespace and common punctuation.
3. Severity vocabulary in A11ySense must follow standard levels: `"Moderate"`, not `"Medium"`.

### Proposed Improvement
```python
def check_label_in_name(visible_text: str, accessible_name: str) -> bool:
    if not visible_text:
        return True
    
    clean_visible = re.sub(r'[^\w\s]', '', visible_text).strip().lower()
    clean_name = re.sub(r'[^\w\s]', '', accessible_name).strip().lower()
    
    # WCAG 2.5.3 requires visible text to be contained within accessible name
    return clean_visible in clean_name
```

---

## 3. Item C: Heading Order Hierarchy (`screen-reader-broken-headings`)

### Code Reference
- File: `backend/app/core/skills/implementations/screen_reader.py`
- Lines: ~620–650 (`Heading Hierarchy Validation`)

### Current Behavior
When heading levels skip (e.g. an `<h1>` is followed directly by an `<h3>` without an `<h2>`), this is often reported as a WCAG Level A violation under SC 1.3.1.

### Accessibility Standard (WCAG Understanding 1.3.1 & Advisory Technique G141)
- The WCAG Working Group has explicitly clarified that **skipping heading levels is an advisory technique (G141)**, not a failure of SC 1.3.1.
- SC 1.3.1 requires that headings are programmatically determined as headings (using `<h1-h6>` or `role="heading"`), but does not mandate strict sequential numbering.
- Classifying skipped headings as a regulatory failure causes audit disputes and developer distrust.

### Proposed Improvement
- Classify `screen-reader-broken-headings` strictly as:
  - `kind`: `"best-practice"`
  - `level`: `"Best Practice"`
  - `wcag_sc`: `None` (or Advisory G141 reference)
  - `severity`: `"Moderate"`
- Wording should recommend maintaining sequential hierarchy for ease of navigation without citing non-compliance.

---

## 4. Item D: Focus Indicator Visibility (`focus-invisible`)

### Code Reference
- File: `backend/app/core/skills/implementations/keyboard_nav.py`
- Lines: ~240–270 (`Verification 4: Verify Focus Visibility`)

### Current Behavior
Inspects computed CSS properties on the focused element:
- `outline-style`, `outline-width`, `box-shadow`, `border`, `background-color`.
- If none of these properties show a detected change between blurred and focused states, it flags `focus-invisible`.

### Limitations & False Positives
1. **`:focus-visible` pseudo-class**: Modern CSS frameworks (Tailwind, Material UI, Bootstrap 5) use `:focus-visible` instead of `:focus`. Headless synthetic focus calls (`element.focus()`) do not always trigger `:focus-visible` unless a real keyboard interaction was emulated.
2. **Parent or Pseudo-element Focus Rings**: Custom design systems often apply focus outlines via a parent container (e.g. `.form-group:focus-within`) or `::after` pseudo-elements.
3. **SVG and Canvas Controls**: Focus indicators drawn via SVG `<rect>` or Canvas overlays are completely missed by computed CSS inspection.

### Proposed Improvement
1. Emulate genuine Tab keypresses (`page.keyboard.press("Tab")`) rather than calling JS `.focus()` so browser engines activate `:focus-visible`.
2. Check `element.matches(':focus-visible')`.
3. Capture a bounding-box visual diff (pixel comparison of the element and 4px bounding padding before and after focus). If pixel delta > 2%, a visible indicator exists.

---

## 5. Item E: Dynamic Disclosure & Expanded State Detection

### Code Reference
- File: `backend/app/core/skills/implementations/screen_reader.py` (lines ~505–540)
- File: `backend/app/core/skills/implementations/keyboard_nav.py` (lines ~380–440)

### Current Behavior
Identifies accordion buttons or dropdown triggers and tests whether `aria-expanded` transitions from `"false"` to `"true"` on keyboard activation (Enter/Space) or click.

### Limitations & False Positives
1. **Framework Synthetic Event Dispatch**: React, Vue, and Angular frequently bind click/keyboard handlers at the root container level. Emulating a low-level mouse click on an inner element may not propagate if hydration has not completed or if synthetic events require standard bubbling.
2. **Animation / Asynchronous Delay**: Accordions with smooth slide animations may delay updating `aria-expanded` until after CSS transitions complete.
3. **Single-Page App Re-renders**: Dynamic disclosure triggers that replace the button DOM node on expansion can cause headless script references to go stale.

### Proposed Improvement
1. Wait for `aria-expanded` attribute changes with a 300ms transition timeout:
   ```javascript
   await page.waitForFunction(
       el => el.getAttribute('aria-expanded') === 'true',
       triggerElement,
       { timeout: 500 }
   ).catch(() => null);
   ```
2. Check both keyboard activation (`Enter`, `Space`) and click handlers before asserting failure.
3. If the button element is detached during expansion, verify whether the newly mounted replacement reflects the expanded state.
