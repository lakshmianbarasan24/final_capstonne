"""
Token Budget and Latency Profiling Module.
Calculates token consumption, trajectory steps, and P95 latency.
Verifies the efficiency rule: Multi-Agent <= 3x tokens and <= 3x latency vs Baseline.
"""

import numpy as np
from typing import List, Dict, Any

class TokenTracker:
    def __init__(self, max_token_budget_per_request: int = 1500, p95_latency_threshold_ms: float = 4500.0):
        self.max_token_budget = max_token_budget_per_request
        self.p95_latency_threshold = p95_latency_threshold_ms
        self.runs = []

    def record_run(self, system_type: str, tokens: int, latency_ms: float, steps: int):
        self.runs.append({
            "system": system_type,
            "tokens": tokens,
            "latency_ms": latency_ms,
            "steps": steps
        })

    def get_summary(self, system_type: str) -> Dict[str, Any]:
        matched = [r for r in self.runs if r["system"] == system_type]
        if not matched:
            return {"count": 0, "avg_tokens": 0, "p95_latency_ms": 0, "avg_steps": 0}

        tokens = [r["tokens"] for r in matched]
        latencies = [r["latency_ms"] for r in matched]
        steps = [r["steps"] for r in matched]

        return {
            "count": len(matched),
            "total_tokens": sum(tokens),
            "avg_tokens": round(float(np.mean(tokens)), 1),
            "max_tokens": max(tokens),
            "avg_latency_ms": round(float(np.mean(latencies)), 2),
            "p95_latency_ms": round(float(np.percentile(latencies, 95)), 2),
            "avg_steps": round(float(np.mean(steps)), 1),
            "within_token_budget": max(tokens) <= self.max_token_budget,
            "within_p95_threshold": float(np.percentile(latencies, 95)) <= self.p95_latency_threshold
        }

    def compare_multi_vs_baseline(self) -> Dict[str, Any]:
        multi_stats = self.get_summary("multi_agent")
        base_stats = self.get_summary("baseline")

        token_ratio = (multi_stats["avg_tokens"] / base_stats["avg_tokens"]) if base_stats["avg_tokens"] > 0 else 1.0
        latency_ratio = (multi_stats["p95_latency_ms"] / base_stats["p95_latency_ms"]) if base_stats["p95_latency_ms"] > 0 else 1.0

        passes_efficiency_gate = (token_ratio <= 3.0) and (latency_ratio <= 3.0)

        return {
            "multi_agent": multi_stats,
            "baseline": base_stats,
            "token_ratio": round(token_ratio, 2),
            "latency_ratio": round(latency_ratio, 2),
            "passes_efficiency_gate": passes_efficiency_gate,
            "rule": "Multi-agent must not exceed 3x tokens or latency without proportional quality gain."
        }
