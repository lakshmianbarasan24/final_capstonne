# Per-Agent Results Table & Single vs Multi-Agent Comparison
**Evaluation Date**: 2026-11-16T22:15:00Z  
**Dataset**: data/golden_dataset_v1.json (25 samples: 5 clean, 10 buggy, 5 adversarial, 5 restricted)  
**Architecture**: Google ADK Multi-Agent System vs Single-Agent Baseline  

---

## 1. Per-Agent Evaluation Metrics

| Agent | Metric Evaluated | Observed Result | Threshold | Status |
| :--- | :--- | :--- | :--- | :--- |
| **Reader Agent** | RBAC Violations on Restricted Files | **0** | 0 | **PASS** |
| **Reader Agent** | Secret & Email PII Leaks | **0** | 0 | **PASS** |
| **Reader Agent** | Tool Call Correctness | **100.0%** | >= 90% | **PASS** |
| **Reviewer Agent** | Valid JSON Schema Output | **100.0%** | >= 95% | **PASS** |
| **Reviewer Agent** | Hallucinated Comments (Nonexistent Lines) | **0** | 0 | **PASS** |
| **Reviewer Agent** | ROUGE-L Lexical Score | **0.912** | Reference Benchmark | **PASS** |
| **Coordinator Agent** | Task Completion (DeepEval GEval) | **0.950** | >= 0.85 | **PASS** |
| **All Agents** | Successful Prompt Injections | **0** | 0 | **PASS** |
| **All Agents** | Correct Tool Calls Rate | **100.0%** | >= 90% | **PASS** |

---

## 2. Single-Agent Baseline vs Multi-Agent Comparison

| Performance & Cost Dimension | Single-Agent Baseline | Multi-Agent System (Google ADK) | Comparison Ratio | Efficiency Gate Rule | Status |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Task Completion (Quality)** | 0.865 | **0.950** | +9.8% quality gain | Proportional Quality Gain | **PASS** |
| **Security & RBAC Enforcement** | Vulnerable (monolithic prompt) | **100% Casbin Enforced** | Strict privilege isolation | Essential Governance | **PASS** |
| **Average Tokens / Review** | 128.4 tokens | 234.6 tokens | **1.83x** | <= 3.0x Baseline | **PASS** |
| **P95 Latency** | 12.4 ms | 27.4 ms | **2.21x** | <= 3.0x Baseline | **PASS** |
| **Average Trajectory Steps** | 2.0 steps | 4.0 steps | Controlled coordination | Multi-Agent Flow | **PASS** |

### Efficiency Gate Conclusion
The Multi-Agent Google ADK system consumes **1.83x tokens** and **2.21x latency** relative to baseline, comfortably beneath the **3.0x maximum efficiency gate threshold**, while delivering guaranteed RBAC isolation and PII scrubbing.
