# Five-Minute Demo Script & Release Recommendation

## Part 1: Five-Minute Demo Script

* **Duration**: 5 Minutes
* **Audience**: AI Release Board, Security Stakeholders, Engineering Leadership

---

### Minute 1: System Overview & Problem Statement
* **Visual**: Present the architecture diagram showing Coordinator Agent, Reader Agent, Reviewer Agent, and FastMCP servers.
* **Talking Points**:
  - Introduce the AI Code Review system built with Google ADK (`google-adk`).
  - Emphasize the core challenge: enforcing strict security boundaries (RBAC and secret masking) while maintaining high-fidelity code review without hallucinated lines.
  - Show the 25-sample golden dataset (`data/golden_dataset_v1.json`).

### Minute 2: Security & Governance in Action (Task 1 & Task 5)
* **Visual**: Run `pytest tests/test_rbac.py tests/test_adversarial.py`.
* **Talking Points**:
  - Demonstrate that when the `reviewer` role requests a restricted file (`restricted_database.py`), Casbin immediately denies access (`RBAC DENIED`).
  - Demonstrate Presidio masking in action: AWS keys and emails are sanitized before reaching the Reviewer agent.
  - Review the structured audit log in `deliverables/audit_log_sample.jsonl` displaying exact cryptographic hashes (SHA-256) for prompt, model, and dataset.

### Minute 3: Agent Evaluation & Multi-Agent vs Baseline (Task 4)
* **Visual**: Open `deliverables/agent_results_table.md`.
* **Talking Points**:
  - Show per-agent metrics: 100% valid JSON, 0 line hallucinations, 0 leaks, DeepEval score 0.885.
  - Compare Multi-Agent vs Single-Agent Baseline: Multi-agent uses 1.8x tokens and 1.4x latency—well within the strict $\le 3\times$ efficiency gate threshold.
  - Highlight Prompt B's superiority over Prompt A in eliminating line-number hallucinations.

### Minute 4: Canary Rollout & SLA Monitoring (Task 6)
* **Visual**: Run `python deployment/canary_simulator.py`.
* **Talking Points**:
  - Show progressive deployment: 10% canary traffic $\to$ 50% $\to$ 100% rollout.
  - Demonstrate SLA checks: P95 latency $< 4500$ ms, error rate $< 2\%$, 0 security breaches.
  - Explain the automated rollback trigger in case of SLA breach.

### Minute 5: Drift Detection & Release Recommendation (Task 7)
* **Visual**: Show `monitoring/drift_detector.py` and `deliverables/incident_note.md`.
* **Talking Points**:
  - Highlight statistical drift detection on the traffic stream using Kolmogorov-Smirnov test (drift detected at request #60).
  - Clarify why this was Data Drift (input distribution shift) rather than an agent regression.
  - Conclude with the formal Release Recommendation.

---

## Part 2: Release Recommendation

### **FINAL DECISION: GO FOR RELEASE**

#### Supporting Evidence Summary:
1. **Security & Governance (100% Pass)**:
   - Zero RBAC violations across all restricted and adversarial samples.
   - Zero PII, secret, or API key leaks.
   - 100% audit log completeness with SHA-256 provenance tracking.
2. **Review Quality & Output Compliance (100% Pass)**:
   - 100% JSON schema validity (exceeding $\ge 95\%$ threshold).
   - Zero hallucinated comments on non-existent lines.
   - DeepEval Task Completion score of **0.885** (exceeding $\ge 0.85$ threshold).
3. **Operational Efficiency (100% Pass)**:
   - Multi-agent token overhead is $1.82\times$ baseline (within $< 3\times$ gate).
   - P95 latency is $1.41\times$ baseline (within $< 3\times$ gate).
4. **Adversarial Resilience (100% Pass)**:
   - Successfully repelled all 5 manual adversarial vectors and all 10 automated red-teaming jailbreak attempts.
