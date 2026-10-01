# Browser Skill

The Browser Skill allows the agent to interact with a web browser to navigate pages and perform actions like a human user.

## Capabilities
- **navigate(url)**: Moves the browser to a specific URL.
- **click(selector)**: Clicks on a specific element identified by a CSS selector.
- **scroll(direction)**: Scrolls the page up or down.
- **get_accessibility_tree()**: Retrieves the ARIA tree of the current page.

## Best Practices
- Wait for `networkidle` before performing actions.
- Use precise CSS selectors.
- Always check if the page has loaded successfully.
