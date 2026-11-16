"""
RBAC Test Suite.
Verifies Casbin RBAC enforcement:
- 'reviewer' role is DENIED restricted files and sensitive configs.
- 'admin' role is ALLOWED access across all paths.
- 'reviewer' role is ALLOWED access to public and clean sample code.
"""

import sys
from pathlib import Path
import pytest

BASE_DIR = Path(__file__).parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from security.rbac_guard import enforce_rbac
from agents.reader_agent import ReaderAgent

@pytest.fixture
def reader():
    return ReaderAgent()

def test_reviewer_denied_restricted_files(reader):
    """Verify that reviewer role is blocked on restricted files."""
    restricted_paths = [
        "data/samples/restricted/restricted_keys.py",
        "data/samples/restricted/restricted_database.py",
        "data/samples/restricted/restricted_admin_auth.py",
        "data/samples/restricted/restricted_oauth.py",
        "data/samples/restricted/restricted_customer_pii.py",
        ".env",
        "secrets/passwords.txt"
    ]
    for path in restricted_paths:
        allowed, reason = enforce_rbac("reviewer", path, "read")
        assert not allowed, f"Security Breach: reviewer was granted access to {path}"
        assert "RBAC DENIED" in reason

        # Also test Reader Agent tool level response
        res = reader.execute(filepath=path, role="reviewer")
        assert res["status"] == "DENIED"
        assert "RBAC_ERROR" in res["content"]

def test_admin_allowed_restricted_files(reader):
    """Verify that admin role is permitted access to files."""
    admin_paths = [
        "data/samples/restricted/restricted_keys.py",
        "data/samples/clean/clean_calc.py"
    ]
    for path in admin_paths:
        allowed, reason = enforce_rbac("admin", path, "read")
        assert allowed, f"False Negative: admin was denied access to {path}"

def test_reviewer_allowed_public_samples(reader):
    """Verify that reviewer role can access standard code samples."""
    public_paths = [
        "data/samples/clean/clean_calc.py",
        "data/samples/clean/clean_user_service.py",
        "data/samples/buggy/buggy_sql.py"
    ]
    for path in public_paths:
        allowed, reason = enforce_rbac("reviewer", path, "read")
        assert allowed, f"Reviewer improperly denied on public file: {path}"
        res = reader.execute(filepath=path, role="reviewer")
        assert res["status"] == "SUCCESS"
