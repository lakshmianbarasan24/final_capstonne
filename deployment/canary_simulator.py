"""
Canary Rollout Simulation and Automated Rollback Controller.
Simulates traffic rollout across three stages:
- Stage 1: 10% Canary traffic (90% Baseline)
- Stage 2: 50% Canary traffic (50% Baseline)
- Stage 3: 100% Canary traffic (Full release)
Enforces SLA:
- P95 Latency <= 4500 ms
- Error / Invalid JSON Rate <= 2.0%
- Security / PII Breaches == 0
Automatically triggers rollback to single-agent baseline if SLA is breached.
Emits deliverables/canary_rollback_log.json.
"""

import sys
import json
import time
import random
from pathlib import Path
from typing import Dict, Any, List

BASE_DIR = Path(__file__).parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from agents.coordinator_agent import CoordinatorAgent
from agents.baseline_agent import SingleAgentBaseline

SLA_CONFIG = {
    "max_p95_latency_ms": 4500.0,
    "max_error_rate_pct": 2.0,
    "max_security_breaches": 0
}

def simulate_canary_rollout(total_requests_per_stage: int = 50) -> Dict[str, Any]:
    print("=" * 60)
    print("STARTING CANARY ROLLOUT SIMULATION (10% -> 50% -> 100%)")
    print("=" * 60)

    dataset_path = BASE_DIR / "data" / "golden_dataset_v1.json"
    with open(dataset_path, "r", encoding="utf-8") as f:
        dataset = json.load(f)

    samples = dataset["samples"]
    coord = CoordinatorAgent(prompt_version="B")
    base = SingleAgentBaseline()

    stages = [
        {"stage": "10% Canary", "canary_pct": 0.10},
        {"stage": "50% Canary", "canary_pct": 0.50},
        {"stage": "100% Full Rollout", "canary_pct": 1.00}
    ]

    rollout_logs = []
    rollback_triggered = False
    rollback_reason = ""

    for s_info in stages:
        stage_name = s_info["stage"]
        canary_pct = s_info["canary_pct"]
        print(f"\n---> Executing {stage_name} ({total_requests_per_stage} synthetic traffic requests)...")

        latencies = []
        errors = 0
        security_breaches = 0
        canary_routed = 0
        baseline_routed = 0

        for i in range(total_requests_per_stage):
            sample = random.choice(samples)
            filepath = sample["filename"]
            is_canary = random.random() < canary_pct

            if is_canary:
                canary_routed += 1
                res = coord.review_file(filepath, role="reviewer")
            else:
                baseline_routed += 1
                res = base.review_file(filepath, role="reviewer")

            lat = res["trajectory"]["latency_ms"]
            latencies.append(lat)

            if res["status"] == "SUCCESS" and not res.get("is_valid_json"):
                errors += 1

            if sample["is_restricted"] and res["status"] != "DENIED":
                security_breaches += 1

        p95_latency = sorted(latencies)[int(0.95 * len(latencies))]
        error_rate = (errors / total_requests_per_stage) * 100

        # Check SLA
        sla_passed = (
            p95_latency <= SLA_CONFIG["max_p95_latency_ms"]
            and error_rate <= SLA_CONFIG["max_error_rate_pct"]
            and security_breaches == SLA_CONFIG["max_security_breaches"]
        )

        stage_record = {
            "stage": stage_name,
            "canary_percent": int(canary_pct * 100),
            "requests_total": total_requests_per_stage,
            "canary_routed": canary_routed,
            "baseline_routed": baseline_routed,
            "p95_latency_ms": round(p95_latency, 2),
            "error_rate_pct": round(error_rate, 2),
            "security_breaches": security_breaches,
            "sla_passed": sla_passed
        }
        rollout_logs.append(stage_record)

        print(f"     [Metrics] P95 Latency: {p95_latency:.2f}ms | Error Rate: {error_rate:.1f}% | Security Breaches: {security_breaches}")

        if not sla_passed:
            rollback_triggered = True
            rollback_reason = f"SLA breached at {stage_name} (p95: {p95_latency:.1f}ms, errors: {error_rate:.1f}%, breaches: {security_breaches})"
            print(f"     [ALERT] SLA BREACH! Triggering automated rollback: {rollback_reason}")
            break
        else:
            print(f"     [STATUS] {stage_name} passed all SLA gates.")

    final_report = {
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "sla_configuration": SLA_CONFIG,
        "stages": rollout_logs,
        "rollback_triggered": rollback_triggered,
        "rollback_reason": rollback_reason if rollback_triggered else "None (All SLA criteria met)",
        "final_deployment_status": "ROLLED_BACK" if rollback_triggered else "DEPLOYED_100_PERCENT"
    }

    out_file = BASE_DIR / "deliverables" / "canary_rollback_log.json"
    out_file.parent.mkdir(parents=True, exist_ok=True)
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(final_report, f, indent=2)

    print("=" * 60)
    print(f"Canary simulation log written to {out_file}")
    return final_report

if __name__ == "__main__":
    simulate_canary_rollout()
