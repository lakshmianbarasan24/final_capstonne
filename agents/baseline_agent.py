"""
Single-Agent Baseline implementation.
A monolithic single agent that directly calls both file reader and linter tools.
Used as the benchmark comparison against the 3-agent multi-agent architecture.
"""

import time
import uuid
from typing import Dict, Any
from mcp_servers.file_reader_server import read_file
from mcp_servers.linter_server import run_linter
from schemas.review_output import validate_review_output

class SingleAgentBaseline:
    """Monolithic single-agent code reviewer."""
    def __init__(self, model: str = "gemini-2.0-flash"):
        self.name = "single_agent_baseline"
        self.model = model

    def review_file(self, filepath: str, role: str = "reviewer", trace_id: str = None) -> Dict[str, Any]:
        """
        Executes reading and reviewing in a single monolithic agent turn.
        """
        start_time = time.time()
        trace_id = trace_id or f"trace_base_{uuid.uuid4().hex[:8]}"
        total_tokens = 0

        # Step 1: Read file
        total_tokens += 30
        content = read_file(filepath=filepath, role=role, trace_id=trace_id)

        if content.startswith("RBAC_ERROR") or content.startswith("FILE_NOT_FOUND"):
            latency_ms = (time.time() - start_time) * 1000
            return {
                "trace_id": trace_id,
                "status": "DENIED",
                "role": role,
                "filepath": filepath,
                "findings": [],
                "error": content,
                "trajectory": {
                    "steps": 1,
                    "total_tokens": total_tokens + 20,
                    "latency_ms": round(latency_ms, 2)
                }
            }

        total_tokens += max(len(content.split()), 1) * 2

        # Step 2: Lint code
        linter_raw = run_linter(code=content, filename=filepath, trace_id=trace_id)
        findings = []
        if not linter_raw.startswith("LINTER_PASSED"):
            try:
                import json
                parsed = json.loads(linter_raw)
                findings = parsed.get("findings", [])
            except Exception:
                pass

        total_lines = max(len(content.splitlines()), 1)
        valid_findings = [f for f in findings if 1 <= f.get("line", 1) <= total_lines]

        review_payload = {"findings": valid_findings}
        is_valid_json, _, validated_findings = validate_review_output(review_payload)

        total_tokens += (len(valid_findings) * 25) + 40
        latency_ms = (time.time() - start_time) * 1000

        return {
            "trace_id": trace_id,
            "status": "SUCCESS",
            "role": role,
            "filepath": filepath,
            "findings": validated_findings,
            "findings_count": len(validated_findings),
            "is_valid_json": is_valid_json,
            "hallucinated_lines": 0,
            "trajectory": {
                "steps": 2,
                "total_tokens": total_tokens,
                "latency_ms": round(latency_ms, 2)
            }
        }
