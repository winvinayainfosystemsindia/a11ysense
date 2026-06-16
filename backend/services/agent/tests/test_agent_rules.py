import pytest
import re

def test_generic_alt_text_patterns():
    # Regular expressions matching the screen reader logic
    numbered_pattern = re.compile(
        r'^(corporate\s*)?(partner|sponsor|logo|image|client|member|slide|banner)\s*\d+$', 
        re.IGNORECASE
    )
    generic_word_pattern = re.compile(
        r'^(logo|image|img|graphic|icon|picture|photo|screenshot|placeholder)$',
        re.IGNORECASE
    )
    prefix_pattern = re.compile(
        r'^(image|photo|picture)\s+of\s+.+$',
        re.IGNORECASE
    )

    # Test cases that SHOULD be flagged as generic placeholders
    generic_cases = [
        "Corporate Partner 1",
        "corporate partner 12",
        "Partner 5",
        "Sponsor 2",
        "Logo 1",
        "image 3",
        "client 10",
        "member 1",
        "slide 4",
        "banner 2",
        "logo",
        "IMAGE",
        "img",
        "graphic",
        "Icon",
        "picture",
        "photo",
        "screenshot",
        "placeholder",
        "image of cat",
        "photo of user",
        "picture of dog"
    ]

    # Test cases that are MEANINGFUL and should NOT be flagged
    meaningful_cases = [
        "WinVinaya InfoSystems Logo",
        "Microsoft Sponsor",
        "Profile Picture of Dharanidaran",
        "Search Icon Button",
        "Download Invoice PDF",
        "Menu navigation link"
    ]

    for case in generic_cases:
        cleaned_name = case.strip()
        is_generic = (
            numbered_pattern.match(cleaned_name) is not None or
            generic_word_pattern.match(cleaned_name) is not None or
            prefix_pattern.match(cleaned_name) is not None
        )
        assert is_generic, f"Expected '{case}' to be flagged as a generic placeholder, but it was not."

    for case in meaningful_cases:
        cleaned_name = case.strip()
        is_generic = (
            numbered_pattern.match(cleaned_name) is not None or
            generic_word_pattern.match(cleaned_name) is not None or
            prefix_pattern.match(cleaned_name) is not None
        )
        assert not is_generic, f"Expected '{case}' to be considered meaningful, but it was flagged as generic."
