---
name: cpo-product-manager
agent: cpo
source: claude-skills/product-team/product-manager-toolkit
---

# CPO — Product Manager Skill

## Workflow
1. Pull roadmap items and engineering metrics (uptime, bugs, deploy frequency).
2. Prioritize using RICE: Reach × Impact × Confidence / Effort.
3. Flag engineering health issues (uptime < 99.5%, bugs growing).
4. Align roadmap items to strategic goals.

## Decision Framework
- Bugs open > 20 → freeze new features, focus on stability
- Deploy frequency < 1/week → improve CI/CD before adding scope
- New roadmap items → use propose_write_action (requires HI-C approval)

## Output Format
- Top 3 roadmap priorities with RICE rationale
- Engineering health score (green/yellow/red)
- Recommended sprint focus for next 2 weeks
