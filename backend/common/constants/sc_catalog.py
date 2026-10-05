"""
Success Criteria Catalog for A11ySense AI.
Contains plain-English metadata for all 50 WCAG criteria across:
- A11YSENSE_AUDIT_SCOPE (26 automated criteria)
- A11YSENSE_MANUAL_REVIEW_CRITERIA (24 manual review criteria)

Follows strict non-technical writing rules:
Zero developer jargon. Banned words (case-insensitive):
aria, dom, attribute, selector, tag, markup, role, tabindex, node,
element id, wcag, axe, semantic, programmatic, contrast ratio.
"""

SC_CATALOG = {
    # ── Automated Scope (26 criteria) ─────────────────────────────────────────
    "1.1.1": {
        "plain_name": "Picture and icon descriptions",
        "what_we_check": "Every picture, button icon, and graphic has a short text description.",
        "expected": "Every picture and graphic should have a short text description explaining what it shows. When a screen reader reaches the picture, it announces this text clearly. This allows people who cannot see the screen to understand the content and enjoy the full story.",
        "manual_steps": [
            "Open the page in your browser.",
            "Start NVDA or JAWS screen reader.",
            "Press G to move from one picture to the next across the page.",
            "Listen to what the screen reader announces for each picture.",
            "Confirm that every informative picture announces a clear description and decorative pictures are skipped."
        ],
    },
    "1.2.1": {
        "plain_name": "Audio-only and video-only alternative",
        "what_we_check": "Recorded sound files and silent video clips have a written transcript or text alternative.",
        "expected": "Every recorded voice track or silent video clip should include a written text description or transcript. People who cannot hear the sound or see the video can read the transcript instead. This ensures everyone gets the same information without missing key details.",
        "manual_steps": [
            "Open the page containing the media player.",
            "Locate the sound recording or silent video clip.",
            "Look for a text transcript link or summary directly below the player.",
            "Open the transcript and compare it to the spoken content or visual actions.",
            "Check that all spoken words and important sounds are fully written out."
        ],
    },
    "1.2.2": {
        "plain_name": "Captions for recorded videos",
        "what_we_check": "Recorded videos with sound have accurate captions synchronized with the speech.",
        "expected": "Recorded video clips should have accurate closed captions timed with the spoken sound. When the video plays, people who cannot hear the sound can read the words on screen in real time. This keeps deaf users informed without guessing.",
        "manual_steps": [
            "Open the page and start playing the video.",
            "Turn on the closed captions button on the video player toolbar.",
            "Watch the captions as people speak on screen.",
            "Confirm the captions match all spoken dialogue and identify background noises.",
            "Check that the text remains readable and stays in sync with the sound."
        ],
    },
    "1.3.1": {
        "plain_name": "Page structure and headings",
        "what_we_check": "Headings, lists, tables, and form labels are properly structured so screen readers announce them correctly.",
        "expected": "The page structure should clearly distinguish headings, bullet lists, data tables, and input labels. When a screen reader user moves through the page, the screen reader announces these sections clearly. This allows users to scan through headings and jump directly to the content they want.",
        "manual_steps": [
            "Open the page with NVDA or JAWS running.",
            "Press H to jump through headings and verify the topic flow.",
            "Press T to navigate into any tables and check that column names are read before cell data.",
            "Press F to move into form fields and listen for clear field names.",
            "Confirm every section announces its type and boundaries clearly."
        ],
    },
    "1.3.4": {
        "plain_name": "Screen orientation flexibility",
        "what_we_check": "The page works in both tall upright mode and wide sideways mode without forcing one view.",
        "expected": "The page should adapt smoothly whether the screen is held tall or turned wide. A person with a mobile device mounted on a wheelchair can view and use the website comfortably in their preferred angle. This removes physical barriers and avoids neck strain.",
        "manual_steps": [
            "Open the page on a mobile device or tablet.",
            "Turn the device from upright view to wide view.",
            "Verify all buttons, menus, and text adjust without getting cut off.",
            "Check that the site does not display a message demanding to turn the phone back.",
            "Confirm all functions remain easy to tap and read in both views."
        ],
    },
    "1.3.5": {
        "plain_name": "Input field autofill hints",
        "what_we_check": "Personal detail fields like name, email, and address help browser autofill fill them in automatically.",
        "expected": "Fields asking for personal details like name, phone, and address should support browser autofill. When filling out a form, a user can let their browser fill in common details with one click. This saves effort for people with motor or memory difficulties.",
        "manual_steps": [
            "Open the form page in your browser.",
            "Click into the first name or email input field.",
            "Observe whether the browser offers saved profile details to autofill.",
            "Select an autofill suggestion and check that each field receives the right information.",
            "Confirm the form accepts the filled details without unexpected errors."
        ],
    },
    "1.4.1": {
        "plain_name": "Information not based on color alone",
        "what_we_check": "Color is not the only way information, errors, or active states are shown.",
        "expected": "Any information shown with color should also have text labels or distinct shapes. When an error occurs or a link is active, a person who is color blind can see an icon or read words explaining the status. This avoids confusion when colors look similar.",
        "manual_steps": [
            "Open the page and review required fields, links, and system warnings.",
            "Look for any element where red, green, or color is the only indicator.",
            "Check if an exclamation icon or clear text accompanies every colored alert.",
            "Verify that links inside paragraphs have underlines or distinct cues beyond color.",
            "Confirm all statuses can be understood in black and white mode."
        ],
    },
    "1.4.2": {
        "plain_name": "Audio control for background sound",
        "what_we_check": "Sounds that play automatically for longer than three seconds can be paused, stopped, or muted.",
        "expected": "Any sound that starts playing automatically should have an easy pause or mute control. A screen reader user can immediately pause the background sound so they can hear their speech software. This prevents loud music from drowning out screen reader announcements.",
        "manual_steps": [
            "Open the page and observe if any audio or music starts on its own.",
            "If sound begins, press Tab to check for an immediate pause or mute button at the top.",
            "Activate the mute button and verify the sound stops.",
            "Ensure the screen reader speech remains clear and understandable.",
            "Confirm the site remembers the mute preference across pages."
        ],
    },
    "1.4.3": {
        "plain_name": "Text color contrast",
        "what_we_check": "Words stand out clearly against their background color so they are easy to read.",
        "expected": "All text should stand out clearly against its background with strong color difference. A person with low vision can comfortably read paragraphs, headings, and button labels without eye strain. This ensures text remains crisp even under bright sunlight.",
        "manual_steps": [
            "Open the page and inspect light grey, muted, or faint text elements.",
            "Examine buttons, links, and placeholder text across headers and banners.",
            "Verify that text remains easily readable from a normal reading distance.",
            "Check that small text has strong contrast against dark or busy background pictures.",
            "Confirm that text does not wash out when highlighted or focused."
        ],
    },
    "1.4.4": {
        "plain_name": "Text zoom up to two hundred percent",
        "what_we_check": "Text can be zoomed to double its size without overlapping or vanishing off the screen.",
        "expected": "Text on the page should enlarge up to double its normal size without words overlapping or disappearing. People who need larger letters can zoom in using their browser settings and read comfortably. This keeps words organized on the screen without horizontal scrolling.",
        "manual_steps": [
            "Open the page in your browser.",
            "Press Control and Plus key repeatedly until zoom reaches two hundred percent.",
            "Scroll down the page and examine text blocks, headers, and menus.",
            "Confirm that no sentences overlap or get clipped behind adjoining containers.",
            "Verify all interactive buttons remain clickable and visible on screen."
        ],
    },
    "1.4.12": {
        "plain_name": "Text spacing flexibility",
        "what_we_check": "Words remain readable when line, word, and letter spacing are widened by user styles.",
        "expected": "The page should allow wider letter, word, and line spacing without cutting off words. People with dyslexia or reading difficulties can adjust spacing to make reading easier. This ensures text does not get clipped inside fixed-size buttons or boxes.",
        "manual_steps": [
            "Open the page in the browser.",
            "Apply wider line height and word spacing settings.",
            "Review headings, buttons, and callout boxes across the layout.",
            "Check that sentences expand naturally without getting cut off at the edges.",
            "Confirm that all buttons still show their complete label clearly."
        ],
    },
    "2.1.1": {
        "plain_name": "Keyboard access for all controls",
        "what_we_check": "Every link, button, menu item, and form input can be reached and activated using only the keyboard.",
        "expected": "Every interactive control on the page should be usable with just the keyboard. A person who cannot use a mouse can press Tab to reach every button and press Enter or Space to activate it. This gives equal access to people who navigate without a mouse.",
        "manual_steps": [
            "Open the page and unplug or put aside your mouse.",
            "Press Tab repeatedly to move forward through all links, buttons, and inputs.",
            "Press Shift+Tab to verify you can also move backwards through controls.",
            "Press Enter or Space on buttons and links to confirm they activate.",
            "Check that popup menus and dropdowns can be opened and closed with the keyboard."
        ],
    },
    "2.1.2": {
        "plain_name": "No keyboard traps",
        "what_we_check": "Keyboard focus never gets permanently stuck inside any popup, video player, or dialog.",
        "expected": "Keyboard focus should never get trapped inside any box, popup, or widget. When a user tabs into a dialog or media player, they can easily press Tab or Escape to exit and continue. This prevents users from getting locked out of the rest of the page.",
        "manual_steps": [
            "Open the page and press Tab until focus enters any popup dialog or media window.",
            "Navigate through all options inside the window using Tab and arrow keys.",
            "Press Tab past the last control or press Escape to close the window.",
            "Verify that focus smoothly returns to the main page content.",
            "Confirm you never have to refresh the page or use a mouse to escape."
        ],
    },
    "2.2.1": {
        "plain_name": "Adjustable time limits",
        "what_we_check": "Users are warned before sessions time out and can easily extend the limit.",
        "expected": "Any automatic countdown or session timer should give an early warning with a simple option to extend. A person who types slowly or needs extra time to read can ask for more time before losing their work. This prevents frustrating logouts during important tasks.",
        "manual_steps": [
            "Open a timed process such as a multi-step form or checkout flow.",
            "Wait until a timeout warning dialog appears on screen.",
            "Check that the warning alerts screen reader users and displays countdown text.",
            "Press the button to extend the session by several minutes.",
            "Confirm the session stays open and previously entered answers remain intact."
        ],
    },
    "2.2.2": {
        "plain_name": "Pause moving and updating content",
        "what_we_check": "Auto-playing carousels, scrolling tickers, and moving banners have a visible pause button.",
        "expected": "Any moving banner, animated slideshow, or scrolling ticker should have a visible pause button. A person with attention or visual difficulties can freeze the motion so they can read in peace. This stops distracting animations from pulling attention away from main tasks.",
        "manual_steps": [
            "Open the page and locate any rotating carousel or scrolling ticker.",
            "Look for a pause or stop button near the moving area.",
            "Press the pause button using keyboard or mouse.",
            "Verify that the slide rotation or ticker stops moving immediately.",
            "Confirm you can still move through slides manually using next and previous buttons."
        ],
    },
    "2.4.1": {
        "plain_name": "Bypass repeated blocks",
        "what_we_check": "A skip link is provided at the very top of the page to jump straight to main content.",
        "expected": "The page should provide a skip link as the very first interactive control. A keyboard or screen reader user can press Tab once, hit Enter, and bypass long navigation menus straight to the main story. This saves dozens of repetitive key presses on every page load.",
        "manual_steps": [
            "Open the page and press Tab once right after loading.",
            "Look for a visible 'Skip to content' link appearing at the top of the window.",
            "Press Enter on the skip link.",
            "Press Tab again and verify focus lands directly on the main heading or article.",
            "Listen to your screen reader to confirm it announces the main section immediately."
        ],
    },
    "2.4.2": {
        "plain_name": "Clear and helpful page title",
        "what_we_check": "The page has a short, meaningful title that announces the specific page topic on load.",
        "expected": "Each page should have a short, clear title that says exactly what the page is about. When the page opens, a screen reader user hears it straight away and knows they are in the right place. This saves time and avoids confusion when many browser tabs are open.",
        "manual_steps": [
            "Open the page in your browser.",
            "Start NVDA or JAWS screen reader.",
            "Press NVDA+T in NVDA or Insert+T in JAWS to hear the page title.",
            "Verify the title names the specific page followed by the website name.",
            "Confirm the title is distinct from other pages on the same website."
        ],
    },
    "2.4.3": {
        "plain_name": "Logical focus order",
        "what_we_check": "Pressing the Tab key moves forward through buttons and links in a natural, logical order.",
        "expected": "Pressing Tab should move smoothly through interactive items in a logical order that matches the reading flow. A keyboard user can predict where focus will land next as they fill out forms and browse links. This prevents surprising jumps that cause users to miss content.",
        "manual_steps": [
            "Open the page and start pressing Tab from the top.",
            "Follow the outline as it moves from one control to the next.",
            "Check that focus flows naturally from top to bottom and left to right.",
            "Ensure focus does not jump erratically between distant page corners.",
            "Confirm that closing a popup returns focus back to the button that opened it."
        ],
    },
    "2.4.4": {
        "plain_name": "Clear link purpose",
        "what_we_check": "Link text explains where the link leads so users do not have to guess its destination.",
        "expected": "Every link should have descriptive text that explains where it leads. When a screen reader user listens to a list of links, they immediately understand each destination without reading the surrounding paragraph. This prevents vague phrases like 'click here' or 'read more'.",
        "manual_steps": [
            "Open the page with NVDA or JAWS running.",
            "Press Insert+F7 in JAWS or NVDA+F7 in NVDA to open the links list.",
            "Review the list of link names in the dialog.",
            "Check that each link name makes sense on its own without seeing the page.",
            "Confirm there are no repeated vague links like 'click here' leading to different places."
        ],
    },
    "2.4.7": {
        "plain_name": "Visible focus indicator",
        "what_we_check": "A clear outline or highlight shows which button, link, or input currently has focus.",
        "expected": "A clear visible ring or outline should surround whichever element currently has focus. A keyboard user can see at a glance where they are on the page as they press Tab. This ensures users never lose track of where their keystrokes will go.",
        "manual_steps": [
            "Open the page and press Tab to begin navigating through links and buttons.",
            "Watch each element as it receives focus.",
            "Verify a strong, clear outline or background change highlights the focused item.",
            "Check that the outline is not hidden by nearby banners or footers.",
            "Confirm the indicator remains clearly visible against all background colors."
        ],
    },
    "2.5.3": {
        "plain_name": "Spoken name matches visible label",
        "what_we_check": "The hidden name read by screen readers matches the visible text written on the button.",
        "expected": "The spoken label announced by a screen reader should include the exact visible words written on the button. A speech-control user can speak the words they see on screen to activate the button without trouble. This prevents a mismatch between what eyes see and what ears hear.",
        "manual_steps": [
            "Open the page and inspect buttons and links that have visible text.",
            "Turn on your screen reader and focus on each button.",
            "Listen to the announced name and compare it to the visible text label.",
            "Verify that the announced name starts with or contains the visible words.",
            "Confirm speech commands speaking the visible label activate the control reliably."
        ],
    },
    "3.1.1": {
        "plain_name": "Primary page language",
        "what_we_check": "The page declares its main human language so screen readers use the correct accent and voice.",
        "expected": "The page should identify its primary human language in its document header. A screen reader can automatically pick the right pronunciation rules, accent, and voice synthesizer. This avoids confusing foreign accents when reading native text.",
        "manual_steps": [
            "Open the page in the browser with NVDA or JAWS running.",
            "Listen to how words are pronounced across main headings and paragraphs.",
            "Check that the voice synthesizer speaks with the correct language accent.",
            "Ensure words are not mispronounced with incorrect phonetics.",
            "Confirm the text reads smoothly from start to finish."
        ],
    },
    "3.1.2": {
        "plain_name": "Language of specific phrases",
        "what_we_check": "Words or sentences in a foreign language are tagged so screen readers switch pronunciation.",
        "expected": "Any quote or phrase in a different language should indicate which language it uses. When a screen reader reaches the foreign phrase, it briefly switches pronunciation so the words sound natural. This helps bilingual listeners understand imported phrases accurately.",
        "manual_steps": [
            "Locate foreign language quotes, phrases, or names on the page.",
            "Listen to how the screen reader pronounces the foreign words.",
            "Verify that the speech synthesizer switches pronunciation for the phrase.",
            "Confirm that normal surrounding text returns to the primary language voice.",
            "Check that the phrase sounds understandable to native speakers of that language."
        ],
    },
    "3.3.2": {
        "plain_name": "Clear form labels and instructions",
        "what_we_check": "Form fields have permanent labels and clear instructions on required formats.",
        "expected": "Every form field should have a permanent text label and helpful instructions on expected formats. When a user fills out dates or phone numbers, they know what format is required before submitting. This helps people complete forms smoothly without trial and error.",
        "manual_steps": [
            "Open the form page and review every text box, dropdown, and checkbox.",
            "Confirm that each field has a visible label that stays visible while typing.",
            "Check for helpful format examples next to fields like dates or phone numbers.",
            "Verify that required fields are clearly noted in plain text.",
            "Listen with a screen reader to confirm all instructions are read out upon focus."
        ],
    },
    "4.1.1": {
        "plain_name": "Clean document structure",
        "what_we_check": "Document markup is clean without duplicate identifiers that break assistive technology.",
        "expected": "The underlying page markup should be cleanly formed without duplicate identification names. Assistive technology like screen readers can parse the page without crashing or skipping sections. This guarantees that all users experience a stable and reliable website.",
        "manual_steps": [
            "Open the page in your browser.",
            "Navigate through all forms, dialogs, and interactive widgets.",
            "Check that form labels stay connected to their corresponding inputs.",
            "Confirm that screen readers do not repeat or skip controls unexpectedly.",
            "Verify that all buttons and links perform their expected action reliably."
        ],
    },
    "4.1.2": {
        "plain_name": "Name, role, and state for custom widgets",
        "what_we_check": "Custom menus, tabs, and toggles announce their identity, purpose, and open or closed state.",
        "expected": "Every interactive control should announce its name, its type, and whether it is currently open or closed. A blind user pressing a menu button hears that it is a button and whether the menu is expanded. This gives blind users the same immediate feedback sighted users receive visually.",
        "manual_steps": [
            "Open the page and use Tab to reach custom dropdowns, tabs, or accordion buttons.",
            "Listen to the announcement: verify it tells you the control name and its type.",
            "Press Space or Enter to open the widget.",
            "Confirm the screen reader announces that the control is now expanded or opened.",
            "Press Escape or Space again and verify it announces that the control is collapsed."
        ],
    },

    # ── Manual Review Scope (24 criteria) ─────────────────────────────────────
    "1.2.3": {
        "plain_name": "Audio description for recorded video",
        "what_we_check": "Recorded video with important visual actions has a narrator describing what happens on screen.",
        "expected": "Videos containing visual action without spoken explanation should offer an audio description track. A blind viewer can listen to a narrator describe physical gestures, scene changes, and on-screen text during natural pauses. This brings movies and tutorials to life for blind audiences.",
        "manual_steps": [
            "Open the video player and look for an audio description track option.",
            "Play the video and watch for scenes with visual action and no talking.",
            "Listen for spoken narration describing what the actors are doing.",
            "Check that the visual descriptions fit neatly into quiet moments without talking over dialogue.",
            "Confirm on-screen titles and text graphics are read aloud by the narrator."
        ],
    },
    "1.2.4": {
        "plain_name": "Captions for live video broadcasts",
        "what_we_check": "Live streaming video has real-time captions so deaf viewers can follow live events.",
        "expected": "Live video broadcasts should provide real-time captions as events happen. A deaf viewer watching a live news broadcast or webinar can read what the speakers are saying with minimal delay. This ensures equal access to live breaking news and company meetings.",
        "manual_steps": [
            "Join the live video stream or webcast.",
            "Turn on the live captioning feature in the video player.",
            "Compare the displayed captions to the live spoken audio.",
            "Check that captions keep pace with speakers with minimal delay.",
            "Confirm important speaker names and sound effects are included in the live text."
        ],
    },
    "1.2.5": {
        "plain_name": "Audio description track for recorded video",
        "what_we_check": "All recorded video stories include dedicated spoken descriptions of visual storytelling.",
        "expected": "Recorded video presentations should include a dedicated narration track explaining all visual story elements. Blind users can listen to the audio track and understand who entered the room, what facial expressions occurred, and what text appeared on screen. This provides a complete storytelling experience.",
        "manual_steps": [
            "Start playing the recorded presentation or video story.",
            "Switch the audio settings to the secondary audio description channel.",
            "Listen to the secondary voice during quiet scenes between character lines.",
            "Confirm key visual plots, gestures, and settings are clearly described.",
            "Verify the extra audio does not drown out the primary sound track."
        ],
    },
    "1.3.2": {
        "plain_name": "Meaningful reading sequence",
        "what_we_check": "The reading order announced by screen readers follows the natural visual meaning of the content.",
        "expected": "The order in which text is read aloud should match the visual and logical flow of the story. A screen reader user hears headings, paragraphs, and side notes in a sensible sequence that makes sense. This prevents side banners from interrupting the middle of a sentence.",
        "manual_steps": [
            "Open the page and activate your screen reader.",
            "Press the down arrow key to read line by line through multi-column articles.",
            "Check that text in the first column finishes before reading the second column.",
            "Verify that side notes and ads do not cut into the middle of main paragraphs.",
            "Confirm the overall meaning remains clear when experienced purely by listening."
        ],
    },
    "1.3.3": {
        "plain_name": "Instructions independent of sensory traits",
        "what_we_check": "Directions do not rely solely on shape, size, location, or sound such as 'click the green circle on the right'.",
        "expected": "Instructions should describe items by their name or purpose rather than just their shape or screen position. When a guide says 'select Submit to continue', a blind user can find the Submit button easily without needing to know it is a round blue button on the right. This keeps directions useful for everyone.",
        "manual_steps": [
            "Read through help text, tutorials, and instructions on the page.",
            "Look for directions referencing only visual cues like 'the round button' or 'the box on the right'.",
            "Verify that every instruction also gives the element's actual text label.",
            "Ensure sound cues like chimes also have visual or written confirmation.",
            "Confirm any user can follow the steps without needing to see the screen layout."
        ],
    },
    "1.4.5": {
        "plain_name": "Real text instead of pictures of text",
        "what_we_check": "Actual text is used instead of static image graphics of words whenever possible.",
        "expected": "Words should be presented as real text rather than baked into image pictures. Users can change text size, adjust colors, and have their screen reader speak the words naturally. This avoids fuzzy, blurry letters when zooming into pictures of text.",
        "manual_steps": [
            "Inspect banners, callout tiles, and promotional graphics across the page.",
            "Try highlighting the text on banners with your mouse cursor.",
            "If text cannot be highlighted, verify if it is an image picture of words.",
            "Check whether logos and branding are the only exceptions using image text.",
            "Confirm that normal headlines and messages use real styled text."
        ],
    },
    "1.4.10": {
        "plain_name": "Reflow without horizontal scrolling",
        "what_we_check": "Content reflows into a single column at four hundred percent zoom without horizontal scrolling.",
        "expected": "The page should re-flow into a single readable column when zoomed up to four hundred percent. A user with severe low vision can read down the page smoothly without having to scroll sideways for every line of text. This makes long articles easy and comfortable to read.",
        "manual_steps": [
            "Open the browser window and set its width to twelve hundred and eighty pixels.",
            "Zoom in using Control and Plus key until the zoom level reaches four hundred percent.",
            "Scroll down through all paragraphs and main content areas.",
            "Check that you do not have to scroll left and right to read lines of text.",
            "Verify that all buttons and menus remain fully usable inside the single column."
        ],
    },
    "1.4.11": {
        "plain_name": "Non-text contrast for buttons and graphics",
        "what_we_check": "Icons, buttons, and form borders stand out clearly against neighboring colors.",
        "expected": "Button boundaries, input outlines, and essential icons should stand out clearly against background surfaces. People with reduced vision can easily tell where a text box begins and distinguish buttons from decorative shapes. This makes form filling effortless and clear.",
        "manual_steps": [
            "Review form field borders, checkbox outlines, and standalone icon buttons.",
            "Verify that the boundary lines of input fields are clearly visible against the page background.",
            "Check that active tab outlines and slider controls have strong visual definition.",
            "Examine icon graphics to ensure their outlines stand out distinctly.",
            "Confirm you can spot every interactive control without squinting."
        ],
    },
    "1.4.13": {
        "plain_name": "Hover and focus popup control",
        "what_we_check": "Tooltips and popups that appear on hover can be dismissed with Escape and remain hovered without disappearing.",
        "expected": "Any tooltip or preview box that appears when hovering should stay visible while moving the mouse over it and close cleanly with Escape. A user reading a tooltip can move their pointer across it without it disappearing abruptly. This avoids accidental popups that block the view.",
        "manual_steps": [
            "Hover your mouse pointer over an element that displays a tooltip or popup menu.",
            "Move the pointer directly into the popup box without it closing.",
            "Press the Escape key on your keyboard to dismiss the popup without moving the mouse.",
            "Verify the popup stays visible until dismissed or mouse is moved away.",
            "Confirm the popup does not cover other critical text unexpectedly."
        ],
    },
    "2.1.4": {
        "plain_name": "Single character key shortcut controls",
        "what_we_check": "Shortcuts using a single letter key can be turned off or customized to prevent accidental triggers.",
        "expected": "Single-key shortcuts should allow turning off or changing to multi-key combinations. A speech-input user speaking words naturally will not accidentally trigger shortcuts like deleting emails or submitting forms. This protects users from unexpected commands while talking.",
        "manual_steps": [
            "Review the site settings or help documentation for keyboard shortcut lists.",
            "Look for shortcuts that fire from a single letter key without Control or Alt.",
            "Check if settings offer an option to turn off single-key shortcuts.",
            "Verify if single keys can be customized with modifier keys.",
            "Test typing in input fields to confirm single letter shortcuts do not activate while typing."
        ],
    },
    "2.3.1": {
        "plain_name": "Three flashes or below threshold",
        "what_we_check": "Animations and video clips do not flash rapidly more than three times per second.",
        "expected": "Content should never flash or strobe more than three times in a single second. People with photosensitive seizure conditions can browse safely without fear of triggering medical seizures. This ensures the website remains a safe environment for all visitors.",
        "manual_steps": [
            "Review videos, banners, and interactive animations across the site.",
            "Watch for rapid flickering, bright strobing, or fast flashing effects.",
            "Confirm that no effect flashes more than three times within any one second window.",
            "Check that saturated red flashes are completely avoided.",
            "Ensure emergency alerts use steady glows rather than rapid strobe effects."
        ],
    },
    "2.4.5": {
        "plain_name": "Multiple ways to find pages",
        "what_we_check": "Users can find pages using at least two different methods, such as a search bar, sitemap, or navigation menu.",
        "expected": "Websites should offer multiple ways to find pages, such as a top navigation bar, a search box, and a sitemap link. A user who finds menus confusing can type keywords into the search box or browse a flat list of pages in the sitemap. This lets everyone navigate in the way that suits them best.",
        "manual_steps": [
            "Open the home page and look for the main navigation menu.",
            "Look for a search input field in the top header area.",
            "Scroll down to the footer to check for a sitemap or table of contents link.",
            "Try locating a specific subpage using both the search box and the navigation menu.",
            "Confirm that at least two distinct ways exist to reach every page."
        ],
    },
    "2.4.6": {
        "plain_name": "Helpful headings and labels",
        "what_we_check": "Section headings and input labels describe their topic or purpose clearly.",
        "expected": "Headings and form labels should clearly state the topic of the section or what information belongs in the field. Users browsing the page can glance at headers and immediately understand how the content is organized. This reduces reading time and makes finding answers quick.",
        "manual_steps": [
            "Read through all headings and subheadings from top to bottom.",
            "Verify that each heading clearly names the topic discussed in that section.",
            "Examine all form labels and check that they clearly describe what to enter.",
            "Confirm there are no vague headings like 'Details' without context.",
            "Check that headings are worded consistently across related sections."
        ],
    },
    "2.5.1": {
        "plain_name": "Simple pointer gestures",
        "what_we_check": "Actions that use multi-touch gestures like pinch-to-zoom also have single-tap buttons.",
        "expected": "Any action triggered by complex motions like pinching, swiping, or rotating should also have simple single-click buttons. A person with motor challenges using a head-pointer or eye-gaze system can tap simple plus and minus buttons instead of pinching. This ensures all interactive features remain accessible.",
        "manual_steps": [
            "Test interactive maps, sliders, and image galleries on a touchscreen.",
            "Look for features requiring multi-finger pinch, two-finger twist, or dragging.",
            "Check for visible single-tap buttons like plus, minus, or arrows nearby.",
            "Verify you can perform the full action using only single taps.",
            "Confirm that single-click buttons provide the exact same functionality."
        ],
    },
    "2.5.2": {
        "plain_name": "Pointer cancellation and undo",
        "what_we_check": "Clicking or tapping an item only fires when the pointer is released, allowing users to cancel by moving away.",
        "expected": "Actions should trigger when a tap or click is released rather than when first pressed down. A user who accidentally touches the wrong button can slide their finger away before lifting it to cancel the action safely. This protects users from accidental clicks and unintentional purchases.",
        "manual_steps": [
            "Press down your mouse button on an interactive control without letting go.",
            "While holding the button down, slide your mouse pointer away from the control.",
            "Release the mouse button while outside the control area.",
            "Verify that the control does not fire its action.",
            "Confirm you can cancel any click before releasing your touch."
        ],
    },
    "2.5.4": {
        "plain_name": "Motion actuation alternative",
        "what_we_check": "Actions triggered by shaking or tilting the device also have ordinary buttons on screen.",
        "expected": "Functions triggered by shaking or tilting the phone should also have standard on-screen buttons and an option to disable motion controls. A person with tremors or whose phone is fixed to a wheelchair mount can tap an on-screen button instead of shaking the device. This prevents accidental triggers caused by unsteady hands.",
        "manual_steps": [
            "Review features that suggest shaking or tilting the device to undo or refresh.",
            "Check for a regular button on screen that performs the same action.",
            "Go to application settings and check for an option to turn off motion controls.",
            "Verify the on-screen button works reliably without moving the device.",
            "Confirm natural movement of the device does not trigger unintended actions."
        ],
    },
    "3.2.1": {
        "plain_name": "No unexpected change on focus",
        "what_we_check": "Moving keyboard focus onto a link, button, or field does not suddenly submit forms or navigate to a new page.",
        "expected": "Moving keyboard focus to a control should never trigger unexpected actions like submitting a form or jumping to a new page. A keyboard user tabbing through options can review fields without surprise popups or page reloads. This creates a predictable and calm browsing experience.",
        "manual_steps": [
            "Open the page and use Tab to move through all links, buttons, and inputs.",
            "Pay close attention as focus lands on each control.",
            "Confirm that simply tabbing onto an item does not open new windows or submit data.",
            "Ensure dialog popups only open when you deliberately press Enter or Space.",
            "Verify the page stays steady until you choose to activate something."
        ],
    },
    "3.2.2": {
        "plain_name": "No unexpected change on input",
        "what_we_check": "Entering text, checking a box, or choosing a dropdown option does not suddenly change context without warning.",
        "expected": "Changing a form value or picking a dropdown option should not automatically reload the page or open a new window without advance notice. Users can select options comfortably and press a deliberate Submit button when they are ready. This prevents disorienting jumps while filling out forms.",
        "manual_steps": [
            "Locate dropdown menus, checkboxes, and radio buttons across the forms.",
            "Use keyboard arrow keys to select different options inside dropdowns.",
            "Check whether choosing an option immediately redirects the browser.",
            "Confirm that selecting an option waits for a Submit button press before submitting.",
            "Verify any automatic update is clearly explained to the user before they make a choice."
        ],
    },
    "3.2.3": {
        "plain_name": "Consistent navigation across pages",
        "what_we_check": "Navigation menus and repeated header links appear in the same order on every page of the website.",
        "expected": "Navigation menus, search bars, and footer links should appear in the exact same order on every page. Users can develop muscle memory and know exactly where to find common links as they move through the site. This avoids confusion caused by menus shifting around.",
        "manual_steps": [
            "Open the home page and note the order of top menu links.",
            "Navigate to three different subpages across the site.",
            "Check the top navigation menu on each page to verify the links stay in the same sequence.",
            "Examine the footer links to confirm they remain organized consistently.",
            "Verify search buttons and utility links maintain their familiar locations."
        ],
    },
    "3.2.4": {
        "plain_name": "Consistent identification of components",
        "what_we_check": "Icons, buttons, and features that perform the same action use identical names across all pages.",
        "expected": "Features that do the same thing should always have the same icon, label, and accessible name on every page. When a search button has a magnifying glass and says Search on one page, it should not say Find or use a different icon on another page. This helps users recognize familiar tools instantly.",
        "manual_steps": [
            "Identify common recurring features like search, shopping cart, and contact links.",
            "Check how these buttons are labeled across different sections of the website.",
            "Verify that the same icon and text label are used for each recurring action.",
            "Listen with a screen reader to confirm the announced name is identical everywhere.",
            "Ensure users do not encounter conflicting names for the same action."
        ],
    },
    "3.3.1": {
        "plain_name": "Clear error identification",
        "what_we_check": "When form errors happen, the problem field is clearly identified and the issue is explained in plain text.",
        "expected": "When an error occurs during form submission, the system should clearly identify which field failed and explain what is wrong in plain text. A screen reader user can immediately hear the error message and know which box needs fixing. This saves people from searching through forms to find what went wrong.",
        "manual_steps": [
            "Open a form and leave required fields blank, then attempt to submit.",
            "Check that error messages appear directly next to the fields that need attention.",
            "Verify the error text clearly explains what went wrong in plain words.",
            "Listen with a screen reader to confirm the error summary is announced immediately.",
            "Confirm focus moves to the first invalid field so you can fix it right away."
        ],
    },
    "3.3.3": {
        "plain_name": "Helpful error suggestions",
        "what_we_check": "Error messages provide constructive suggestions on how to correct mistakes whenever possible.",
        "expected": "When input errors are detected, the system should offer helpful guidance on how to fix them correctly. If someone enters an invalid date or phone number format, the message should show an example of the right format. This guides users toward success without frustration.",
        "manual_steps": [
            "Enter an invalid date, email, or telephone format into form fields.",
            "Submit the form and read the resulting error message.",
            "Verify the message suggests the correct format, such as showing 'use month-day-year'.",
            "Follow the suggestion, enter the corrected text, and resubmit.",
            "Confirm the form accepts the suggested format smoothly."
        ],
    },
    "3.3.4": {
        "plain_name": "Error prevention for legal and financial actions",
        "what_we_check": "Submissions involving money, legal agreements, or sensitive personal data can be reviewed, reversed, or confirmed.",
        "expected": "Forms that involve financial payments, legal commitments, or deleting personal data should provide a review step before finalizing. A user can double-check account numbers and totals on a confirmation screen and fix typos before money moves. This prevents costly mistakes that cannot be undone.",
        "manual_steps": [
            "Navigate through a checkout flow or sensitive settings update.",
            "Proceed to the final submission step.",
            "Verify that a summary screen shows all entered data for review before confirming.",
            "Check that you can easily edit details from the summary screen without restarting.",
            "Confirm that critical delete or transfer actions require a clear confirmation step."
        ],
    },
    "4.1.3": {
        "plain_name": "Status messages announced to screen readers",
        "what_we_check": "Alerts, shopping cart updates, and search result counters are announced to screen reader users without shifting focus.",
        "expected": "Status updates like 'three results found' or 'item added to cart' should be announced automatically by screen readers without moving the user's cursor. A blind user shopping online hears immediate confirmation that their item was added while staying in place on the page. This keeps users informed without disrupting their flow.",
        "manual_steps": [
            "Open a search or shopping page with your screen reader active.",
            "Type a query into an instant search box or click an 'Add to Cart' button.",
            "Do not move your mouse or press any keys after clicking.",
            "Listen to confirm your screen reader announces the status message automatically.",
            "Check that your keyboard focus stays right where it was without jumping away."
        ],
    },
    "2.4.11": {
        "plain_name": "Focused controls not hidden by sticky banners",
        "what_we_check": "When navigating with the keyboard, the focused button or field is not completely covered by floating headers, footers, or cookie banners.",
        "expected": "Controls with keyboard focus should remain visible and not be completely hidden behind sticky headers, footers, or floating dialogs. A keyboard user moving through the page can always see the highlighted item they are interacting with.",
        "manual_steps": [
            "Open the page and use the Tab key to navigate through all interactive controls.",
            "Observe the keyboard focus indicator as you move past sticky headers or footers.",
            "Check whether any focused button or link gets completely hidden beneath a floating banner.",
            "Confirm that the page scrolls sufficiently to keep the focused item in view."
        ],
    },
    "2.5.7": {
        "plain_name": "Dragging actions have single-click alternatives",
        "what_we_check": "Actions that require dragging items, like reordering lists or moving sliders, can also be completed with simple clicks or taps.",
        "expected": "Any function that requires dragging or sliding should provide a simple click or tap alternative, such as up and down arrow buttons. People who cannot hold and drag can tap buttons to move items easily.",
        "manual_steps": [
            "Locate drag-and-drop features, sortable lists, or range sliders on the page.",
            "Check for alternative buttons, such as Move Up, Move Down, or clickable step buttons.",
            "Use the alternative buttons to complete the action without dragging.",
            "Confirm the changes save and update properly."
        ],
    },
    "2.5.8": {
        "plain_name": "Target size and spacing for buttons",
        "what_we_check": "Clickable buttons, icons, and links have enough size or spacing so users do not tap the wrong item accidentally.",
        "expected": "Clickable targets should be large enough or have sufficient spacing around them. A person with motor challenges or anyone using a touchscreen can tap buttons accurately without accidentally triggering adjacent links.",
        "manual_steps": [
            "Examine small icons, close buttons, and inline links across the page.",
            "Check that adjacent clickable items have sufficient space between them.",
            "Tap or click on each button to verify it responds without triggering neighboring controls."
        ],
    },
    "3.2.6": {
        "plain_name": "Consistent help and contact information",
        "what_we_check": "Help features like chat, contact numbers, and FAQ links appear in the same relative position across all pages.",
        "expected": "Self-help options, contact details, and support chat links should appear in the same location on every page where they are offered. Users who need assistance can find help quickly without searching across different page sections.",
        "manual_steps": [
            "Locate support links, chat widgets, or contact numbers on the home page.",
            "Navigate to several subpages across the site.",
            "Verify that the help links or chat widgets appear in the same location on every page."
        ],
    },
    "3.3.7": {
        "plain_name": "No redundant data entry",
        "what_we_check": "Information entered in a multi-step process is auto-populated or available for selection rather than re-typed.",
        "expected": "Information previously entered in the same session, such as a shipping address, should be auto-populated or selectable in subsequent steps. Users do not have to type the same details repeatedly across multi-step checkout or registration forms.",
        "manual_steps": [
            "Navigate through a multi-step checkout or application process.",
            "Enter your address or contact information in the initial step.",
            "Proceed to subsequent steps and verify the previously entered details are pre-filled or selectable without re-typing."
        ],
    },
    "3.3.8": {
        "plain_name": "Accessible login without memory puzzles",
        "what_we_check": "Logging in does not require solving cognitive puzzles, memorizing complex patterns, or transcribing difficult text.",
        "expected": "Authentication processes should support password managers, copy-paste, or one-click email links instead of requiring users to solve puzzles or transcribe text. People with cognitive impairments can sign in smoothly and securely.",
        "manual_steps": [
            "Navigate to the login or sign-in screen.",
            "Verify that password fields allow pasting from password managers.",
            "Check that alternative login methods like email magic links, biometric login, or standard credentials are available without cognitive puzzles."
        ],
    },
}
