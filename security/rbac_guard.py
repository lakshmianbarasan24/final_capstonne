"""
Role-Based Access Control (RBAC) Guard.
Supports Casbin library with a self-contained fallback matcher.
Enforces that 'reviewer' cannot access restricted files, while 'admin' is permitted.
"""

import os
import re
from pathlib import Path
from typing import Tuple

# Try loading Casbin if installed
try:
    import casbin
    _HAS_CASBIN = True
except ImportError:
    _HAS_CASBIN = False

MODEL_CONF_DEFAULT = str(Path(__file__).parent.parent / "rbac" / "model.conf")
POLICY_CSV_DEFAULT = str(Path(__file__).parent.parent / "rbac" / "policy.csv")

class CasbinFallbackEnforcer:
    """Fallback enforcer implementing Casbin-compatible keyMatch2 glob matching."""
    def __init__(self, policy_path: str):
        self.policies = []
        self._load_policy(policy_path)

    def _load_policy(self, policy_path: str):
        if not os.path.exists(policy_path):
            return
        with open(policy_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                parts = [p.strip() for p in line.split(",")]
                if len(parts) >= 4 and parts[0] == "p":
                    self.policies.append({
                        "sub": parts[1],
                        "obj": parts[2],
                        "act": parts[3]
                    })

    def _match_pattern(self, obj: str, pattern: str) -> bool:
        if pattern == "*":
            return True
        norm_obj = obj.replace("\\", "/").lstrip("/")
        norm_pat = pattern.replace("\\", "/").lstrip("/")
        # Convert glob style pattern to regex
        regex_pat = "^" + re.escape(norm_pat).replace(r"\*", ".*") + "$"
        return bool(re.match(regex_pat, norm_obj, re.IGNORECASE))

    def enforce(self, sub: str, obj: str, act: str) -> bool:
        sub = sub.lower().strip()
        act = act.lower().strip()
        norm_obj = obj.replace("\\", "/").strip()

        # Hard security boundaries: restricted paths are never allowed for reviewer
        restricted_markers = ["restricted/", "secrets/", ".env", "private_key", "password.txt", "admin_auth"]
        if sub != "admin":
            for marker in restricted_markers:
                if marker in norm_obj.lower():
                    return False

        for pol in self.policies:
            if pol["sub"] == sub or pol["sub"] == "*":
                if pol["act"] == act or pol["act"] == "*":
                    if self._match_pattern(norm_obj, pol["obj"]):
                        return True
        return False


class RBACGuard:
    def __init__(self, model_path: str = MODEL_CONF_DEFAULT, policy_path: str = POLICY_CSV_DEFAULT):
        self.model_path = model_path
        self.policy_path = policy_path
        self.enforcer = None

        if _HAS_CASBIN and os.path.exists(model_path) and os.path.exists(policy_path):
            try:
                self.enforcer = casbin.Enforcer(model_path, policy_path)
            except Exception:
                self.enforcer = CasbinFallbackEnforcer(policy_path)
        else:
            self.enforcer = CasbinFallbackEnforcer(policy_path)

    def is_allowed(self, role: str, filepath: str, action: str = "read") -> Tuple[bool, str]:
        """
        Check if role has permission to access filepath for action.
        Returns: (is_allowed: bool, reason: str)
        """
        role = (role or "reviewer").lower().strip()
        action = (action or "read").lower().strip()
        norm_path = filepath.replace("\\", "/").strip()

        # Check permission
        allowed = bool(self.enforcer.enforce(role, norm_path, action))
        if allowed:
            return True, f"Role '{role}' is authorized for '{action}' on '{filepath}'."
        else:
            return False, f"RBAC DENIED: Role '{role}' lacks '{action}' permissions for restricted file '{filepath}'."


# Global singleton instance
_rbac_singleton = None

def get_rbac_guard() -> RBACGuard:
    global _rbac_singleton
    if _rbac_singleton is None:
        _rbac_singleton = RBACGuard()
    return _rbac_singleton

def enforce_rbac(role: str, filepath: str, action: str = "read") -> Tuple[bool, str]:
    return get_rbac_guard().is_allowed(role, filepath, action)
