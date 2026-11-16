"""
Coordinator Agent implementation using Google ADK.
Orchestrates agent-to-agent workflow:
Client -> Coordinator -> Reader Agent -> Coordinator -> Reviewer Agent -> Coordinator -> Client.
Tracks trajectory cost: step count, total tokens, and wall-clock latency.
"""

import time
import uuid
from typing import Dict, Any, List
from agents.reader_agent import ReaderAgent
from agents.reviewer_agent import ReviewerAgent

COORDINATOR_INSTRUCTION = """You are the Coordinator Agent of the multi-agent code review system.
Your responsibility:
1. Coordinate the end-to-end review lifecycle.
2. Delegate code reading to the Reader Agent.
3. Validate that the Reader Agent succeeded and did not trigger an RBAC breach.
4. Pass sanitized code to the Reviewer Agent.
5. Aggregate the final findings into a structured review response.
"""

class CoordinatorAgent:
    """Google ADK Coordinator Agent."""
    def __init__(self, prompt_version: str = "B", model: str = "gemini-2.0-flash"):
        self.name = "coordinator_agent"
        self.model = model
        self.instruction = COORDINATOR_INSTRUCTION
        self.reader = ReaderAgent(model=model)
        self.reviewer = ReviewerAgent(prompt_version=prompt_version, model=model)

    def review_file(self, filepath: str, role: str = "reviewer", trace_id: str = None) -> Dict[str, Any]:
        """
        Executes end-to-end multi-agent code review workflow.
        """
        start_time = time.time()
        trace_id = trace_id or f"trace_{uuid.uuid4().hex[:8]}"

        trajectory_steps = []
        total_tokens = 0

        # Step 1: Coordinator receives request & delegates to Reader
        trajectory_steps.append({
            "step": 1,
            "agent": self.name,
            "action": "DELEGATE_READ",
            "target": filepath,
            "role": role
        })
        total_tokens += 35

        # Step 2: Reader Agent execution
        reader_res = self.reader.execute(filepath=filepath, role=role, trace_id=trace_id)
        trajectory_steps.append({
            "step": 2,
            "agent": reader_res["agent"],
            "status": reader_res["status"],
            "tokens": reader_res["tokens"]
        })
        total_tokens += reader_res["tokens"]

        # Check if Reader was blocked by RBAC
        if reader_res["status"] == "DENIED":
            latency_ms = (time.time() - start_time) * 1000
            return {
                "trace_id": trace_id,
                "status": "DENIED",
                "role": role,
                "filepath": filepath,
                "findings": [],
                "error": reader_res["content"],
                "trajectory": {
                    "steps": len(trajectory_steps),
                    "total_tokens": total_tokens,
                    "latency_ms": round(latency_ms, 2)
                }
            }

        # Step 3: Coordinator delegates to Reviewer with sanitized code
        trajectory_steps.append({
            "step": 3,
            "agent": self.name,
            "action": "DELEGATE_REVIEW",
            "target": filepath
        })
        total_tokens += 35

        # Step 4: Reviewer Agent execution
        reviewer_res = self.reviewer.execute(
            code=reader_res["content"],
            filename=filepath,
            trace_id=trace_id
        )
        trajectory_steps.append({
            "step": 4,
            "agent": reviewer_res["agent"],
            "status": reviewer_res["status"],
            "tokens": reviewer_res["tokens"]
        })
        total_tokens += reviewer_res["tokens"]

        latency_ms = (time.time() - start_time) * 1000

        return {
            "trace_id": trace_id,
            "status": "SUCCESS",
            "role": role,
            "filepath": filepath,
            "findings": reviewer_res["findings"],
            "findings_count": reviewer_res["findings_count"],
            "is_valid_json": reviewer_res["is_valid_json"],
            "hallucinated_lines": reviewer_res["hallucinated_lines"],
            "trajectory": {
                "steps": len(trajectory_steps),
                "total_tokens": total_tokens,
                "latency_ms": round(latency_ms, 2)
            }
        }
