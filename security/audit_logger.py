"""
Audit Logger Module.
Generates structured JSON logs for all agent tool calls and decisions.
Logs role, tool, target, decision (ALLOW/DENY), execution latency, token counts,
and cryptographic provenance hashes.
"""

import json
import os
import time
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional

from security.provenance import get_provenance_tracker

DEFAULT_LOG_PATH = Path(__file__).parent.parent / "deliverables" / "audit_log_sample.jsonl"
_file_lock = threading.Lock()

class AuditLogger:
    def __init__(self, log_path: Path = DEFAULT_LOG_PATH):
        self.log_path = log_path
        self.log_path.parent.mkdir(parents=True, exist_ok=True)
        self.provenance = get_provenance_tracker()

    def log_tool_call(
        self,
        trace_id: str,
        role: str,
        agent_name: str,
        tool_name: str,
        target: str,
        decision: str,
        reason: str = "",
        input_args: Optional[Dict[str, Any]] = None,
        tokens_used: int = 0,
        latency_ms: float = 0.0,
        prompt_text: str = ""
    ) -> Dict[str, Any]:
        """
        Record a structured audit log entry.
        """
        provenance_data = self.provenance.get_provenance_record(prompt_text)

        log_entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "trace_id": trace_id,
            "role": role,
            "agent": agent_name,
            "tool": tool_name,
            "target": target,
            "decision": decision,  # "ALLOW" or "DENY"
            "reason": reason,
            "tokens_used": tokens_used,
            "latency_ms": round(latency_ms, 2),
            "input_args": input_args or {},
            "provenance": provenance_data
        }

        # Append JSON line to audit log file with thread safety
        with _file_lock:
            with open(self.log_path, "a", encoding="utf-8") as f:
                f.write(json.dumps(log_entry) + "\n")

        return log_entry


_logger_singleton = None

def get_audit_logger() -> AuditLogger:
    global _logger_singleton
    if _logger_singleton is None:
        _logger_singleton = AuditLogger()
    return _logger_singleton
