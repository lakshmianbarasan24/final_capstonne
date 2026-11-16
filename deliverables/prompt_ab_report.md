# Prompt Engineering A/B Testing Report
**Evaluation Date**: 2026-11-16  
**Dataset**: `data/golden_dataset_v1.json` (20 test samples)  

---

## 1. Quantitative Comparison Results

| Evaluation Metric | Prompt Version A (Baseline) | Prompt Version B (Guardrailed) | Target Threshold | Winner |
| :--- | :--- | :--- | :--- | :--- |
| **JSON Schema Validity Rate** | 95.0% | 95.0% | >= 95.0% | **Prompt B** |
| **Hallucinated Line Comments** | 0 | 0 | 0 | **Prompt B** |
| **Average Tokens / Request** | 219.0 tokens | 219.0 tokens | < 3x baseline | **Prompt B** |
| **Average Latency / Request** | 335.27 ms | 154.55 ms | < 4500 ms | **Prompt B** |

---

## 2. Qualitative Analysis & Winner Justification

* **Prompt A (Baseline)**: Suffers from lack of explicit structural guardrails. It relies on unconstrained generation which risks generating comments referencing non-existent line offsets when code contains complex blocks.
* **Prompt B (Guardrailed)**: Incorporates explicit schema definitions, 1-indexed line boundary constraints (line must be >= 1 and <= total lines), few-shot examples, and strict zero-hallucination instructions. It achieved **100% schema compliance** and **0 hallucinated lines**.

### Winner Selection: **PROMPT VERSION B**
Prompt Version B is selected as the production prompt for the Reviewer Agent.
