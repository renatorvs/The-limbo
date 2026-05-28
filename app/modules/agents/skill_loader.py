"""Load SKILL.md files and inject domain expertise into agent prompts."""

from pathlib import Path
from typing import Dict, Optional

SKILLS_DIR = Path(__file__).resolve().parents[2] / "skills"

_cache: Dict[str, str] = {}


def _parse_frontmatter(content: str) -> tuple[dict, str]:
    """Minimal YAML frontmatter parser (key: value lines only)."""
    if not content.startswith("---"):
        return {}, content
    parts = content.split("---", 2)
    if len(parts) < 3:
        return {}, content
    meta = {}
    for line in parts[1].strip().splitlines():
        if ":" in line:
            key, val = line.split(":", 1)
            meta[key.strip()] = val.strip()
    return meta, parts[2].strip()


def load_skill_for_agent(agent_id: str) -> Optional[str]:
    """Load skill body for an agent. Returns None if no skill file found."""
    agent_id = agent_id.lower()
    if agent_id in _cache:
        return _cache[agent_id]

    if not SKILLS_DIR.exists():
        return None

    for path in SKILLS_DIR.glob("*.md"):
        content = path.read_text(encoding="utf-8")
        meta, body = _parse_frontmatter(content)
        if meta.get("agent", "").lower() == agent_id:
            _cache[agent_id] = body
            return body

    return None


def get_skill_context(agent_id: str) -> str:
    """Return skill instructions to append to system prompt."""
    skill = load_skill_for_agent(agent_id)
    if not skill:
        return ""
    return f"\n\n## Domain Skill (claude-skills derived)\n{skill}"
