# Keyboard Navigation Skill

The Keyboard Navigation Skill allows the agent to tab through all interactive elements on a web page to evaluate focus visibility, logical tab order, and detect keyboard traps.

## Capabilities
- **run_keyboard_test(page)**: Simulates tabbing through a page using keyboard interactions.
  - Verifies that each focused element has a visible focus indicator.
  - Detects if focus gets trapped on any element.
  - Checks if the focus order follows logical vertical page flow.

## Best Practices
- Focus the body element first to reset browser tab sequence.
- Include brief delays (e.g. 100ms) between tab presses to allow focus-visible styles to apply.
