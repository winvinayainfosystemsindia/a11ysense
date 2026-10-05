"""
Hard-coded WCAG 2.2 Level A and AA success criteria used by the Excel
"WCAG Criteria Reference" sheet.

Each row: (criterion number, title, level, version it was introduced in, description).
Level A = 31 criteria, Level AA = 24 criteria (55 in total).
4.1.1 Parsing is not listed because WCAG 2.2 removed it.
"""

_PRINCIPLES = {
    "1": "Perceivable",
    "2": "Operable",
    "3": "Understandable",
    "4": "Robust",
}

WCAG22_A_AA_CRITERIA = [
    ("1.1.1", "Non-text Content", "A", "WCAG 2.0", "Every image, icon and other non-text item has a text alternative that gives the same information."),
    ("1.2.1", "Audio-only and Video-only (Prerecorded)", "A", "WCAG 2.0", "Recorded audio-only and video-only content has a text transcript or an audio description."),
    ("1.2.2", "Captions (Prerecorded)", "A", "WCAG 2.0", "Recorded videos with sound have captions."),
    ("1.2.3", "Audio Description or Media Alternative (Prerecorded)", "A", "WCAG 2.0", "Recorded videos have an audio description or a full text alternative."),
    ("1.2.4", "Captions (Live)", "AA", "WCAG 2.0", "Live videos with sound have captions."),
    ("1.2.5", "Audio Description (Prerecorded)", "AA", "WCAG 2.0", "Recorded videos have an audio description for important visual information."),
    ("1.3.1", "Info and Relationships", "A", "WCAG 2.0", "Headings, lists, tables, forms and other structure shown visually are also available to assistive technology."),
    ("1.3.2", "Meaningful Sequence", "A", "WCAG 2.0", "The reading order of the content makes sense when read by a screen reader."),
    ("1.3.3", "Sensory Characteristics", "A", "WCAG 2.0", "Instructions do not depend only on shape, size, position, sound or colour."),
    ("1.3.4", "Orientation", "AA", "WCAG 2.1", "Content works in both portrait and landscape unless one is essential."),
    ("1.3.5", "Identify Input Purpose", "AA", "WCAG 2.1", "Form fields that collect personal details state their purpose so browsers can fill them in."),
    ("1.4.1", "Use of Color", "A", "WCAG 2.0", "Colour is not the only way to show information, an action or an error."),
    ("1.4.2", "Audio Control", "A", "WCAG 2.0", "Audio that plays automatically for more than 3 seconds can be paused, stopped or muted."),
    ("1.4.3", "Contrast (Minimum)", "AA", "WCAG 2.0", "Text has enough contrast against its background (4.5:1, or 3:1 for large text)."),
    ("1.4.4", "Resize Text", "AA", "WCAG 2.0", "Text can be enlarged to 200% without losing content or function."),
    ("1.4.5", "Images of Text", "AA", "WCAG 2.0", "Real text is used instead of pictures of text, unless the image is essential."),
    ("1.4.10", "Reflow", "AA", "WCAG 2.1", "Content fits a narrow screen (320 px wide) without sideways scrolling."),
    ("1.4.11", "Non-text Contrast", "AA", "WCAG 2.1", "Buttons, form borders, icons and charts have at least 3:1 contrast."),
    ("1.4.12", "Text Spacing", "AA", "WCAG 2.1", "Nothing is lost when users increase line, letter, word and paragraph spacing."),
    ("1.4.13", "Content on Hover or Focus", "AA", "WCAG 2.1", "Pop-ups shown on hover or focus can be dismissed, hovered over and stay visible until closed."),
    ("2.1.1", "Keyboard", "A", "WCAG 2.0", "All features can be used with the keyboard alone."),
    ("2.1.2", "No Keyboard Trap", "A", "WCAG 2.0", "Keyboard focus can always be moved away from any part of the page."),
    ("2.1.4", "Character Key Shortcuts", "A", "WCAG 2.1", "Single-key shortcuts can be turned off, changed, or only work when the control has focus."),
    ("2.2.1", "Timing Adjustable", "A", "WCAG 2.0", "Time limits can be turned off, adjusted or extended."),
    ("2.2.2", "Pause, Stop, Hide", "A", "WCAG 2.0", "Moving, blinking or auto-updating content can be paused, stopped or hidden."),
    ("2.3.1", "Three Flashes or Below Threshold", "A", "WCAG 2.0", "Nothing flashes more than three times in one second."),
    ("2.4.1", "Bypass Blocks", "A", "WCAG 2.0", "Users can skip repeated blocks such as menus, for example with a skip link or landmarks."),
    ("2.4.2", "Page Titled", "A", "WCAG 2.0", "Each page has a title that describes its topic or purpose."),
    ("2.4.3", "Focus Order", "A", "WCAG 2.0", "Keyboard focus moves in an order that keeps the meaning and operation of the page."),
    ("2.4.4", "Link Purpose (In Context)", "A", "WCAG 2.0", "The purpose of each link is clear from its text or its surrounding context."),
    ("2.4.5", "Multiple Ways", "AA", "WCAG 2.0", "There is more than one way to find a page, such as a menu, search or site map."),
    ("2.4.6", "Headings and Labels", "AA", "WCAG 2.0", "Headings and labels describe their topic or purpose."),
    ("2.4.7", "Focus Visible", "AA", "WCAG 2.0", "The keyboard focus indicator is always visible."),
    ("2.4.11", "Focus Not Obscured (Minimum)", "AA", "WCAG 2.2", "A control that has keyboard focus is not completely hidden by other content."),
    ("2.5.1", "Pointer Gestures", "A", "WCAG 2.1", "Features that need multi-finger or path gestures also work with a single tap or click."),
    ("2.5.2", "Pointer Cancellation", "A", "WCAG 2.1", "Actions are triggered on release, so users can cancel an accidental press."),
    ("2.5.3", "Label in Name", "A", "WCAG 2.1", "The accessible name of a control contains its visible text label."),
    ("2.5.4", "Motion Actuation", "A", "WCAG 2.1", "Features triggered by shaking or tilting the device also work with normal controls and can be turned off."),
    ("2.5.7", "Dragging Movements", "AA", "WCAG 2.2", "Anything that can be done by dragging can also be done with a single click or tap."),
    ("2.5.8", "Target Size (Minimum)", "AA", "WCAG 2.2", "Clickable targets are at least 24 by 24 pixels, or have enough spacing."),
    ("3.1.1", "Language of Page", "A", "WCAG 2.0", "The main language of each page is set so screen readers use the right voice."),
    ("3.1.2", "Language of Parts", "AA", "WCAG 2.0", "Passages in a different language are marked with that language."),
    ("3.2.1", "On Focus", "A", "WCAG 2.0", "Moving focus to a control does not cause an unexpected change of context."),
    ("3.2.2", "On Input", "A", "WCAG 2.0", "Changing a form value does not cause an unexpected change of context."),
    ("3.2.3", "Consistent Navigation", "AA", "WCAG 2.0", "Navigation menus appear in the same order on every page."),
    ("3.2.4", "Consistent Identification", "AA", "WCAG 2.0", "Items with the same function are labelled the same way across pages."),
    ("3.2.6", "Consistent Help", "A", "WCAG 2.2", "Help options such as contact details appear in the same place on every page."),
    ("3.3.1", "Error Identification", "A", "WCAG 2.0", "Input errors are found automatically and described to the user in text."),
    ("3.3.2", "Labels or Instructions", "A", "WCAG 2.0", "Form fields have clear labels or instructions."),
    ("3.3.3", "Error Suggestion", "AA", "WCAG 2.0", "When an input error is found, a suggestion for fixing it is given."),
    ("3.3.4", "Error Prevention (Legal, Financial, Data)", "AA", "WCAG 2.0", "Legal, financial and data submissions can be reversed, checked or confirmed."),
    ("3.3.7", "Redundant Entry", "A", "WCAG 2.2", "Information already entered in the same process is not asked for again."),
    ("3.3.8", "Accessible Authentication (Minimum)", "AA", "WCAG 2.2", "Logging in does not depend on memorising, transcribing or solving a puzzle."),
    ("4.1.2", "Name, Role, Value", "A", "WCAG 2.0", "Every control exposes its name, role and current state to assistive technology."),
    ("4.1.3", "Status Messages", "AA", "WCAG 2.1", "Status messages are announced by screen readers without moving focus."),
]


def principle_of(sc_code: str) -> str:
    """Returns the WCAG principle for a criterion number."""
    return _PRINCIPLES.get(sc_code.split(".")[0], "N/A")
