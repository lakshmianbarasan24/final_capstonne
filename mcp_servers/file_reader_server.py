"""
FastMCP File Reader Tool Server.
Exposes read_file tool with RBAC enforcement, PII/secret masking, and audit logging.
"""

import os
import time
from pathlib import Path
from fastmcp import FastMCP

from security.rbac_guard import enforce_rbac
from security.pii_masker import mask_pii_and_secrets
from security.audit_logger import get_audit_logger

mcp_reader = FastMCP("FileReaderServer")
BASE_DIR = Path(__file__).parent.parent

@mcp_reader.tool()
def read_file(filepath: str, role: str = "reviewer", trace_id: str = "trace_000") -> str:
    """
    Safely reads source file content.
    Enforces RBAC: 'reviewer' is denied restricted files, 'admin' is allowed.
    Masks secrets, API keys, and PII before returning.
    """
    start_time = time.time()
    logger = get_audit_logger()

    # 1. Normalize and resolve path
    norm_path = filepath.replace("\\", "/").strip()
    full_path = (BASE_DIR / norm_path).resolve()

    # 2. RBAC Enforcement
    is_allowed, rbac_reason = enforce_rbac(role, norm_path, "read")
    if not is_allowed:
        latency = (time.time() - start_time) * 1000
        logger.log_tool_call(
            trace_id=trace_id,
            role=role,
            agent_name="reader_agent",
            tool_name="read_file",
            target=norm_path,
            decision="DENY",
            reason=rbac_reason,
            tokens_used=15,
            latency_ms=latency
        )
        return f"RBAC_ERROR: Access Denied for role '{role}' accessing '{norm_path}'. {rbac_reason}"

    # 3. File existence check
    if not full_path.exists():
        latency = (time.time() - start_time) * 1000
        logger.log_tool_call(
            trace_id=trace_id,
            role=role,
            agent_name="reader_agent",
            tool_name="read_file",
            target=norm_path,
            decision="DENY",
            reason="File not found on disk",
            tokens_used=10,
            latency_ms=latency
        )
        return f"FILE_NOT_FOUND: File '{norm_path}' does not exist."

    # 4. Read file content
    with open(full_path, "r", encoding="utf-8", errors="replace") as f:
        raw_content = f.read()

    # 5. Mask secrets and PII
    masked_content, detected_leaks = mask_pii_and_secrets(raw_content)

    latency = (time.time() - start_time) * 1000
    token_estimate = max(len(masked_content.split()), 1) * 2

    # 6. Structured Audit Log
    logger.log_tool_call(
        trace_id=trace_id,
        role=role,
        agent_name="reader_agent",
        tool_name="read_file",
        target=norm_path,
        decision="ALLOW",
        reason="RBAC authorized; secrets & PII sanitized",
        tokens_used=token_estimate,
        latency_ms=latency,
        input_args={"filepath": norm_path, "role": role, "leaks_masked": len(detected_leaks)}
    )

    return masked_content

if __name__ == "__main__":
    mcp_reader.run()
