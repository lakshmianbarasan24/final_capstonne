# AI Code Review Agent System
### Evaluation, Security Governance, and Production Release Framework

Built with **Google Agent Development Kit (`google-adk`)**, **Google Gemini**, and **Model Context Protocol (FastMCP)**.

---

## 1. Overview & Problem Statement

Modern automated code review systems must accurately identify bugs and stylistic defects while strictly preventing unauthorized access to protected codebases and confidential data. This evaluation framework rigorously quantifies the security boundaries, output fidelity, and operational efficiency of a multi-agent Google ADK system against clean, buggy, and adversarial code samples. Success is defined as achieving zero security or PII breaches, over 95% valid JSON findings, and task completion score $\ge 0.85$ under a strict $3\times$ token and latency budget relative to the single-agent baseline.

---

## 2. System Architecture

The system consists of three specialized Google ADK agents communicating through two isolated FastMCP tool servers, evaluated against a monolithic single-agent baseline:

```
                      +---------------------------------------+
                      |         Inbound Review Request        |
                      |          (role, file_path)            |
                      +---------------------------------------+
                                          |
                                          v
                      +---------------------------------------+
                      |       Coordinator Agent (ADK)         |
                      |   Orchestrates Reader & Reviewer      |
                      +---------------------------------------+
                                  /               \
                       (1) Delegate read      (3) Delegate review
                                /                   \
                               v                     v
          +-------------------------+     +-------------------------+
          |    Reader Agent (ADK)   |     |   Reviewer Agent (ADK)  |
          | Enforces RBAC & Masking |     | Prompt B & Schema Check |
          +-------------------------+     +-------------------------+
                       |                               |
              (McpToolset client)             (McpToolset client)
                       v                               v
          +-------------------------+     +-------------------------+
          | FastMCP File Reader     |     | FastMCP Linter Server   |
          |   - Casbin RBAC Guard   |     |   - AST Static Analysis |
          |   - Presidio PII Masker |     |   - Defect Diagnostic   |
          +-------------------------+     +-------------------------+
```

### Component Roles:
* **Reader Agent (`agents/reader_agent.py`)**: Calls FastMCP file reader tool. Enforces role-based access control (RBAC) via Casbin, blocking `reviewer` from restricted files while permitting `admin`. Scrubs passwords, bearer tokens, API keys, and emails via Microsoft Presidio.
* **Reviewer Agent (`agents/reviewer_agent.py`)**: Calls FastMCP linter tool. Uses hardened Prompt B to emit strict JSON schema outputs (`file`, `line`, `severity`, `comment`) with zero line-number hallucinations.
* **Coordinator Agent (`agents/coordinator_agent.py`)**: Root ADK agent managing task handoff, trajectory tracking (tokens, latency, steps), and review aggregation.
* **Single-Agent Baseline (`agents/baseline_agent.py`)**: Monolithic agent directly executing both tools, used for quality, cost, and latency comparisons.

---

## 3. Project Directory Structure

```
Final-Capstone/
├── .env.example                          # Environment variables template
├── requirements.txt                      # Project dependencies
├── README.md                             # This execution guide
├── AI_Evaluation_Problem_Statement_and_ADK_Plan.md  # Full problem statement & plan
├── rbac/
│   ├── model.conf                        # Casbin RBAC model definition
│   └── policy.csv                        # Role permissions (admin, reviewer)
├── security/
│   ├── rbac_guard.py                     # Casbin RBAC enforcement engine
│   ├── pii_masker.py                     # Presidio PII & secret scrubbing
│   ├── provenance.py                     # SHA-256 provenance tracker
│   ├── audit_logger.py                   # Structlog JSON audit logger
│   └── compliance_checklist.md           # GDPR, SOC2, and residency checklist
├── mcp_servers/
│   ├── file_reader_server.py             # FastMCP file reading tool
│   └── linter_server.py                  # FastMCP AST code analysis tool
├── schemas/
│   └── review_output.py                  # Pydantic & JSON Schema definitions
├── agents/
│   ├── reader_agent.py                   # ADK Reader Agent
│   ├── reviewer_agent.py                 # ADK Reviewer Agent (Prompt A & B)
│   ├── coordinator_agent.py              # ADK Coordinator Agent
│   └── baseline_agent.py                 # ADK Single-Agent Baseline
├── data/
│   ├── problem_statement.txt             # 3-sentence measurable problem statement
│   ├── golden_dataset_v1.json            # 25-sample versioned, read-only dataset
│   ├── validators.py                     # Dataset schema & duplicate validators
│   └── samples/
│       ├── clean/                        # 5 clean samples (clean_calc.py, etc.)
│       ├── buggy/                        # 10 buggy samples (buggy_sql.py, etc.)
│       ├── adversarial/                  # 5 adversarial injection files
│       └── restricted/                   # 5 restricted credential/PII files
├── evaluation/
│   ├── harness.py                        # Async batch evaluation harness
│   ├── prompt_ab_test.py                 # Prompt A vs Prompt B test runner
│   ├── metrics.py                        # ROUGE-L, BLEU, PII & hallucination checks
│   ├── deepeval_runner.py                # DeepEval task completion evaluator
│   └── token_tracker.py                  # Token budget & P95 latency profiler
├── tests/
│   ├── test_rbac.py                      # RBAC verification test suite
│   ├── test_adversarial.py               # 5 required adversarial test cases
│   ├── test_redteam.py                   # 10 automated red-teaming jailbreak tests
│   └── test_quality_gate.py              # CI/CD Quality Gate enforcer
├── deployment/
│   └── canary_simulator.py               # 10% -> 50% -> 100% canary & rollback
├── monitoring/
│   └── drift_detector.py                 # Evidently & SciPy statistical drift engine
└── deliverables/
    ├── golden_dataset_v1.json            # Versioned dataset (in data/)
    ├── agent_results_table.md            # Per-agent & single vs multi comparison
    ├── audit_log_sample.jsonl            # JSON structured audit log records
    ├── security_audit_report.md          # One-page security audit report
    ├── quality_gate_output.txt           # CI/CD Quality Gate pass output
    ├── canary_rollback_log.json          # Canary rollout and SLA log
    ├── incident_note.md                  # Drift incident response note
    ├── demo_script_and_recommendation.md # 5-min demo script & GO recommendation
    ├── prompt_ab_report.md               # Prompt A/B evaluation report
    └── reproducibility_hashes.json       # SHA-256 provenance record
```

---

## 4. Setup & Installation

### Prerequisites
* Python 3.11 or later
* Virtual environment (recommended)

### 1. Clone & Set Up Virtual Environment
```bash
# Windows (PowerShell)
python -m venv .venv
.venv\Scripts\Activate.ps1

# Linux / macOS
python3 -m venv .venv
source .venv/bin/activate
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Environment Configuration
Copy `.env.example` to `.env`:
```bash
cp .env.example .env
```
*(Optionally set your `GEMINI_API_KEY`. The test harness operates in deterministic offline simulation mode when no key is set, and seamlessly switches to live Gemini 2.0 Flash when provided).*

---

## 5. Execution Guide (Step-by-Step Run Commands)

Every task from the problem statement has a dedicated, executable runner:

### Task 1 & 2: Data Curation & Dataset Validation
Validates that the golden dataset has zero duplicates, all required fields, and verified sample counts:
```bash
python data/validators.py
```
*Output*: Validates 25 samples (5 clean, 10 buggy, 5 adversarial, 5 restricted) with 0 duplicates.

---

### Task 3: Prompt Engineering A/B Comparison
Executes Prompt Version A (minimal baseline) vs Prompt Version B (guardrailed schema prompt) across all test samples:
```bash
python evaluation/prompt_ab_test.py
```
*Output*: Generates `deliverables/prompt_ab_report.md` justifying **Prompt Version B** as the winner with 100% JSON compliance and 0 line hallucinations.

---

### Task 4: Comprehensive Multi-Agent Evaluation & Comparison
Executes the asynchronous evaluation harness comparing the Multi-Agent Google ADK system against the Single-Agent Baseline:
```bash
python evaluation/harness.py
```
*Output*: Generates `deliverables/agent_results_table.md` comparing task completion, token usage, and P95 latency.

---

### Task 5: Security, RBAC & Red-Teaming Tests

#### Run Casbin RBAC Test Suite
```bash
pytest tests/test_rbac.py -v
```
*Verifies*: `reviewer` is blocked on restricted files and credentials; `admin` is authorized.

#### Run 5 Required Adversarial Tests
```bash
pytest tests/test_adversarial.py -v
```
*Verifies*: Comment injection, secret reveal request, role escalation, handoff manipulation, and custom polyglot attack.

#### Run 10 Automated Red-Teaming Jailbreak Tests
```bash
pytest tests/test_redteam.py -v
```
*Verifies*: Multi-turn jailbreaks, DAN prompts, base64 obfuscation, and homoglyphs.

#### Run All 18 Test Cases in One Command:
```bash
pytest tests/ -v
```

---

### Task 5: CI/CD Quality Gate Runner
Runs all quality gate assertions defined in Section 5. Fails the build (exit code 1) if any threshold is violated:
```bash
python tests/test_quality_gate.py
```
*Output*: Prints verification table and writes `deliverables/quality_gate_output.txt`.

---

### Task 6: Canary Rollout & SLA Rollback Simulation
Simulates progressive traffic rollout across 10%, 50%, and 100% traffic, evaluating latency, error rates, and automated rollback triggers:
```bash
python deployment/canary_simulator.py
```
*Output*: Emits `deliverables/canary_rollback_log.json`.

---

### Task 7: Post-Production Statistical Drift Detection
Executes Kolmogorov-Smirnov statistical tests on production traffic to detect distribution shifts, classify drift type, and write incident note:
```bash
python monitoring/drift_detector.py
```
*Output*: Generates `deliverables/incident_note.md`.

---

## 6. Metrics & Quality Gate Thresholds (Section 5)

| Metric | Target Threshold | Observed Result | Status |
| :--- | :--- | :--- | :--- |
| **Valid JSON output** | $\ge 95\%$ | **100.0%** | **PASS** |
| **Correct tool calls** | $\ge 90\%$ | **100.0%** | **PASS** |
| **Hallucinated comments** | $0$ on nonexistent lines | **0** | **PASS** |
| **Secret or PII leaks** | $0$ | **0** | **PASS** |
| **RBAC violations** | $0$ | **0** | **PASS** |
| **Successful injections** | $0$ | **0** | **PASS** |
| **Task completion (DeepEval)** | $\ge 0.85$ | **0.950** | **PASS** |
| **Token Budget vs Baseline** | $\le 3.0\times$ | **1.83x** | **PASS** |
| **P95 Latency vs Baseline** | $\le 3.0\times$ | **2.21x** | **PASS** |

---

## 7. Deliverables Index

All 9 deliverables specified in Section 7 have been generated and committed:

| # | Deliverable Name | File Location | Description |
|---|---|---|---|
| 1 | **Versioned Golden Dataset** | `data/golden_dataset_v1.json` | 25 samples (SHA-256 verified, read-only) |
| 2 | **Per-Agent Results Table** | `deliverables/agent_results_table.md` | Metrics breakdown and baseline comparison |
| 3 | **Audit Log Sample** | `deliverables/audit_log_sample.jsonl` | Structured JSON lines with provenance hashes |
| 4 | **Security Audit Report** | `deliverables/security_audit_report.md` | One-page audit covering 5 tests, RBAC, and severities |
| 5 | **Quality Gate Output** | `deliverables/quality_gate_output.txt` | Automated CI/CD gate pass report |
| 6 | **Canary Rollback Log** | `deliverables/canary_rollback_log.json` | 10% -> 50% -> 100% rollout logs and SLA checks |
| 7 | **Drift Analysis & Incident Note** | `deliverables/incident_note.md` | Statistical drift timestamp, type, RCA & CAPA |
| 8 | **Demo Script & Recommendation** | `deliverables/demo_script_and_recommendation.md` | 5-minute presentation script & GO recommendation |
| 9 | **Reproducibility Records** | `deliverables/reproducibility_hashes.json` | SHA-256 hashes of model, dataset, prompt, and deps |

---

## 8. Release Recommendation

### **FINAL DECISION: GO FOR RELEASE**
The system satisfies all 7 quality gate thresholds, adheres to the $\le 3\times$ token and latency efficiency ceiling, and demonstrated zero security vulnerabilities across 18 adversarial tests.
