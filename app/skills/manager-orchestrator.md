---
name: manager-orchestrator
agent: manager
source: claude-skills/engineering/agent-workflow-designer
---

# Manager — Multi-Agent Orchestrator Skill

## Workflow
1. Decompose objective into domain-specific sub-tasks.
2. Delegate to CFO (finance), CMO (growth), CPO (product), CS (retention).
3. Collect findings and resolve conflicts between domains.
4. Present unified recommendation via CEO synthesis.

## Orchestration Patterns
- **Sequential handoff**: each agent builds on prior findings
- **Parallel analysis**: all agents analyze same objective independently (default)
- **Multi-startup**: run parallel analysis per company, then cross-portfolio synthesis

## HI-C Rules
- Any write action (campaign, roadmap, transaction) → propose_write_action
- Strategic decisions with spend/hiring → queue for human approval
- Human can override any agent recommendation at any time
