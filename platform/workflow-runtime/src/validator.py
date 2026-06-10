"""
validator.py — Workflow definition validator

Validates a workflow definition dict against the required structure defined
in schema/workflow-schema.yaml. Returns a list of validation errors.

Capability: CAP-004 (Workflow Orchestration)
Defined by: ADR-005 — Workflow Engine Technology Selection
"""

import re
from typing import Any

WORKFLOW_ID_PATTERN = re.compile(r"^WF-\d{3,}$")
CAPABILITY_ID_PATTERN = re.compile(r"^CAP-\d{3,}$")

REQUIRED_WORKFLOW_FIELDS = ["id", "title", "version", "capability", "steps"]
REQUIRED_STEP_FIELDS = ["id", "name", "command"]


def validate(definition: dict) -> list[str]:
    """
    Validate a workflow definition dict.

    Returns a list of error strings. An empty list means the definition is valid.
    """
    errors: list[str] = []

    if not isinstance(definition, dict):
        return ["Workflow definition must be a YAML mapping."]

    # Required top-level fields
    for field in REQUIRED_WORKFLOW_FIELDS:
        if field not in definition:
            errors.append(f"Missing required field: '{field}'.")

    # Validate id format
    wf_id = definition.get("id", "")
    if wf_id and not WORKFLOW_ID_PATTERN.match(wf_id):
        errors.append(f"Invalid workflow id '{wf_id}'. Expected format: WF-NNN.")

    # Validate capability id format
    cap_id = definition.get("capability", "")
    if cap_id and not CAPABILITY_ID_PATTERN.match(cap_id):
        errors.append(f"Invalid capability id '{cap_id}'. Expected format: CAP-NNN.")

    # Validate version
    version = definition.get("version")
    if version is not None and (not isinstance(version, int) or version < 1):
        errors.append(f"'version' must be an integer >= 1, got: {version!r}.")

    # Validate steps
    steps = definition.get("steps")
    if steps is not None:
        if not isinstance(steps, list) or len(steps) == 0:
            errors.append("'steps' must be a non-empty list.")
        else:
            seen_ids: set[str] = set()
            for i, step in enumerate(steps):
                if not isinstance(step, dict):
                    errors.append(f"Step {i + 1}: must be a mapping.")
                    continue
                for field in REQUIRED_STEP_FIELDS:
                    if field not in step:
                        errors.append(f"Step {i + 1}: missing required field '{field}'.")
                step_id = step.get("id", "")
                if step_id in seen_ids:
                    errors.append(f"Duplicate step id: '{step_id}'.")
                seen_ids.add(step_id)

    return errors


def is_valid(definition: dict) -> bool:
    """Return True if the definition is valid."""
    return len(validate(definition)) == 0
