import yaml
from pathlib import Path
from typing import Any, Dict
from dataclasses import dataclass
from datetime import datetime


class GovernorViolation(Exception):
    """Raised when an action violates the Governor."""


@dataclass
class GovernorDecision:
    allowed: bool
    reason: str
    requires_approval: bool = False


class GovernorEngine:
    """
    Enforces the immutable Governor rules.
    Mika may query this engine but never modify it.
    """

    def __init__(self, governor_path: Path):
        if not governor_path.exists():
            raise FileNotFoundError(f"Governor file not found: {governor_path}")

        with governor_path.open("r", encoding="utf-8") as f:
            self.rules: Dict[str, Any] = yaml.safe_load(f)

        self.version = self.rules["governor"]["version"]
        self.audit_log: list[dict] = []

    # --------------------------------------------------
    # CORE QUERY INTERFACE
    # --------------------------------------------------

    def allows(self, permission_path: str) -> GovernorDecision:
        """
        Example permission_path:
        - "models.create_neural_networks"
        - "tools.execute_code_in_sandbox"
        """

        allowed = self._lookup_permission(permission_path)
        decision = GovernorDecision(
            allowed=allowed,
            reason="allowed" if allowed else "forbidden",
            requires_approval=self._requires_approval(permission_path),
        )

        self._audit("permission_check", permission_path, decision)
        return decision

    def clamp(self, category: str, key: str, value: float) -> float:
        """
        Clamp learning parameters within bounds.
        """
        bounds = (
            self.rules.get("learning_bounds", {})
            .get("personality_clamp", {})
            .get(key)
        )

        if not bounds:
            return value

        min_v, max_v = bounds
        clamped = max(min_v, min(max_v, value))

        self._audit(
            "clamp",
            f"{category}.{key}",
            {"input": value, "output": clamped},
        )

        return clamped

    def requires_approval(self, action: str) -> bool:
        return action in self.rules.get("approval_required_for", [])

    # --------------------------------------------------
    # INTERNALS
    # --------------------------------------------------

    def _lookup_permission(self, path: str) -> bool:
        """
        Traverse permissions tree.
        """
        parts = path.split(".")
        node = self.rules.get("permissions", {})

        try:
            for p in parts:
                node = node[p]
            return True
        except Exception:
            return False

    def _requires_approval(self, path: str) -> bool:
        approvals = self.rules.get("approval_required_for", [])
        return any(path.endswith(a) or a in path for a in approvals)

    def _audit(self, event: str, subject: str, decision: Any):
        self.audit_log.append(
            {
                "time": datetime.utcnow().isoformat(),
                "event": event,
                "subject": subject,
                "decision": str(decision),
            }
        )

    # --------------------------------------------------
    # ENFORCEMENT
    # --------------------------------------------------

    def enforce(self, permission_path: str):
        decision = self.allows(permission_path)

        if not decision.allowed:
            raise GovernorViolation(
                f"Action '{permission_path}' is forbidden by Governor."
            )

        if decision.requires_approval:
            raise GovernorViolation(
                f"Action '{permission_path}' requires human approval."
            )

        return True
