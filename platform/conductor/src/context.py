"""
context.py — Context assembly for Conductor model calls.

Assembles a structured context block from Wyrd stores to inject into every
model call. The richer the Wyrd persona and project data, the more personalised
the conductor responses become.

Context block format (prepended to all model prompts):
  === AIOS Context ===
  Operator: <name>
  Values:   <top 3 declared values>
  Projects: <active PRJ-NNN titles and status>
  Goals:    <active GL-NNN titles>
  Focus:    <active FCA-NNN titles>
  ==================

Capability: CAP-017 (Conductor — Conversational Interface)
Defined by: ADR-013 — Conductor Agent Design, ADR-012 — Wyrd Subsystem Boundary
"""

import sys
from pathlib import Path
from typing import Optional

# ---------------------------------------------------------------------------
# Path resolution — add wyrd/src to path for identity stores
# ---------------------------------------------------------------------------

_REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent
_WYRD_SRC = _REPO_ROOT / "wyrd" / "src"
if str(_WYRD_SRC) not in sys.path:
    sys.path.insert(0, str(_WYRD_SRC))


def assemble_context(
    *,
    persona_store=None,
    project_store=None,
    goal_store=None,
    focus_store=None,
    max_projects: int = 5,
    max_goals: int = 5,
    max_focus: int = 3,
) -> str:
    """
    Assemble a context block string for injection into model calls.

    Stores are optional — if not provided, the corresponding section is
    omitted gracefully. This allows the conductor to function even when
    Wyrd stores are empty or unavailable.

    Parameters
    ----------
    persona_store : PersonaStore, optional
    project_store : ProjectStore, optional
    goal_store : GoalStore, optional
    focus_store : FocusAreaStore, optional
    max_projects : int
        Maximum number of active projects to include.
    max_goals : int
        Maximum number of active goals to include.
    max_focus : int
        Maximum number of active focus areas to include.

    Returns
    -------
    str
        Context block string, or empty string if all stores are empty.
    """
    lines = []

    # -- Persona ------------------------------------------------------------
    if persona_store is not None:
        try:
            persona = persona_store.load()
            if persona:
                name = persona.get("operator_name") or persona.get("name") or "Unknown"
                lines.append(f"Operator: {name}")
                values = (persona.get("declared_values") or [])[:3]
                if values:
                    val_text = "; ".join(
                        v if isinstance(v, str) else v.get("statement", str(v))
                        for v in values
                    )
                    lines.append(f"Values:   {val_text}")
        except Exception:
            pass

    # -- Projects -----------------------------------------------------------
    if project_store is not None:
        try:
            projects = project_store.list_active()[:max_projects]
            if projects:
                proj_lines = [
                    f"  - {p.id} [{p.status}] {p.title}" for p in projects
                ]
                lines.append("Active projects:")
                lines.extend(proj_lines)
        except Exception:
            pass

    # -- Goals --------------------------------------------------------------
    if goal_store is not None:
        try:
            goals = goal_store.list_active()[:max_goals]
            if goals:
                goal_lines = [f"  - {g.id} {g.title}" for g in goals]
                lines.append("Active goals:")
                lines.extend(goal_lines)
        except Exception:
            pass

    # -- Focus areas --------------------------------------------------------
    if focus_store is not None:
        try:
            areas = focus_store.list_active()[:max_focus]
            if areas:
                area_lines = [
                    f"  - {a.id} {a.title}"
                    + (f" [{a.attention_budget}]" if a.attention_budget else "")
                    for a in areas
                ]
                lines.append("Focus areas:")
                lines.extend(area_lines)
        except Exception:
            pass

    if not lines:
        return ""

    header = "=== AIOS Context ==="
    footer = "=" * len(header)
    return "\n".join([header] + lines + [footer])


def inject_context(prompt: str, context_block: str) -> str:
    """Prepend a context block to a prompt. Returns prompt unchanged if block is empty."""
    if not context_block:
        return prompt
    return f"{context_block}\n\n{prompt}"


def build_stores() -> dict:
    """
    Attempt to instantiate all Wyrd stores from default paths.
    Returns a dict with keys: persona_store, project_store, goal_store, focus_store.
    Any store that fails to import returns None.
    """
    stores = {
        "persona_store": None,
        "project_store": None,
        "goal_store": None,
        "focus_store": None,
    }
    try:
        from project_store import PersonaStore
        stores["persona_store"] = PersonaStore()
    except Exception:
        pass
    try:
        from project_store import ProjectStore
        stores["project_store"] = ProjectStore()
    except Exception:
        pass
    try:
        from goal_store import GoalStore
        stores["goal_store"] = GoalStore()
    except Exception:
        pass
    try:
        from goal_store import FocusAreaStore
        stores["focus_store"] = FocusAreaStore()
    except Exception:
        pass
    return stores
