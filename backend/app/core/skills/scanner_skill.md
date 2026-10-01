# Scanner Skill

The Scanner Skill uses the industry-standard `axe-core` engine to perform automated accessibility audits.

## Capabilities
- **run_axe()**: Executes a full WCAG 2.2 audit on the current page.
- **parse_violations()**: Translates raw axe-core JSON into structured internal models.

## Rules
- Focus on high-impact violations first.
- Map every violation to a specific WCAG Success Criterion.
- Provide actionable remediation advice for developers.
