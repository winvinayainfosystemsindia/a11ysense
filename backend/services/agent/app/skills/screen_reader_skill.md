# Screen Reader Simulation Skill

The Screen Reader Simulation Skill allows the agent to simulate the exact text spoken by screen readers (NVDA/JAWS) for all interactive page elements and integrate with local NVDA instances via Windows COM API interfaces.

## Capabilities
- **run_screen_reader_test(page)**: Analyzes interactive elements, computes their spoken screen reader announcements according to the AccName computation standards, speaks them via local NVDA COM wrapper if running, and reports name, role, value mismatches.

## Best Practices
- Verify accessible names on all form controls, links, images, and buttons.
- Flag vague focus target text like "click here" or empty descriptions.
