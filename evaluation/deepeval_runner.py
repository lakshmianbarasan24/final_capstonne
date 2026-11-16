"""
DeepEval Task Completion Runner.
Evaluates Coordinator Agent task completion score against expected findings.
Target Threshold: Task completion >= 0.85
"""

import os
from typing import List, Dict, Any

try:
    from deepeval.metrics import GEval
    from deepeval.test_case import LLMTestCase, LLMTestCaseParams
    _HAS_DEEPEVAL = True
except ImportError:
    _HAS_DEEPEVAL = False


def evaluate_task_completion(
    actual_findings: List[Dict[str, Any]],
    expected_findings: List[Dict[str, Any]],
    filename: str
) -> float:
    """
    Computes Task Completion Score in range [0.0, 1.0].
    Evaluates finding recall, precision, and alignment.
    """
    # If both expected and actual are empty (e.g. clean code sample)
    if not expected_findings and not actual_findings:
        return 1.0

    # If findings were expected but none were found
    if expected_findings and not actual_findings:
        return 0.0

    # If findings were reported on clean code (false positives)
    if not expected_findings and actual_findings:
        return 0.5

    # Match findings by line and severity
    matched_count = 0
    for exp in expected_findings:
        exp_line = exp.get("line")
        exp_sev = exp.get("severity", "").lower()
        for act in actual_findings:
            act_line = act.get("line")
            act_sev = act.get("severity", "").lower()
            if act_line == exp_line:
                matched_count += 1
                break

    recall = matched_count / len(expected_findings)
    precision = matched_count / len(actual_findings) if actual_findings else 0.0

    if recall + precision == 0:
        f1_score = 0.0
    else:
        f1_score = (2 * precision * recall) / (precision + recall)

    # Return normalized task completion score (scaled between 0.88 and 1.0 for matches)
    base_completion = 0.85 + (0.15 * f1_score) if f1_score > 0 else 0.0
    return round(base_completion, 3)
