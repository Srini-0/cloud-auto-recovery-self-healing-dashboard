# Design Document: Cloud Auto-Recovery Dissertation Generator

## Overview

This document describes the design for generating a full university-style dissertation titled **"Cloud Infrastructure Auto-Recovery Dashboard: An Intelligent Self-Healing System for AWS EC2 Instances"**. The output is a single Markdown file at `docs/dissertation.md`, approximately 80–90 pages in length, structured as a formal BCA/B.Tech/MCA final-year project submission.

The Dissertation_Generator is an AI agent (Kiro) that reads the actual codebase — `Backend/app.py`, frontend components, demo scripts, and project documentation — and synthesises all content into a coherent academic document. No external generation tool or template engine is used; the agent writes the document directly using `fsWrite` followed by `fsAppend` calls.

The design covers: generation strategy, document structure, chapter-by-chapter content design, writing approach, and file output strategy.

---

## Architecture

The generation process is a sequential, single-pass pipeline:

```
┌─────────────────────────────────────────────────────────┐
│                  Source Material                         │
│                                                          │
│  Backend/app.py          docs/project-overview.md       │
│  Backend/demo_setup.py   docs/backend-scripts-guide.md  │
│  Backend/requirements.txt                               │
│  src/components/dashboard/*.tsx                         │
└──────────────────────┬──────────────────────────────────┘
                       │ read + analyse
                       ▼
┌─────────────────────────────────────────────────────────┐
│              Dissertation_Generator (Kiro)               │
│                                                          │
│  1. Read all source files                               │
│  2. Write front matter (fsWrite)                        │
│  3. Append chapters 1–10 sequentially (fsAppend)        │
│  4. Append References + Appendix (fsAppend)             │
└──────────────────────┬──────────────────────────────────┘
                       │ writes
                       ▼
┌─────────────────────────────────────────────────────────┐
│              docs/dissertation.md                        │
│              (single Markdown file, ~80-90 pages)        │
└─────────────────────────────────────────────────────────┘
```

The generator does not produce intermediate files. All content is written directly to `docs/dissertation.md`. The initial `fsWrite` call creates the file with the title and front matter; subsequent `fsAppend` calls add each chapter in order.

---

## Components and Interfaces

### Source Reader

The generator reads the following files before writing any content:

| File | Purpose |
|---|---|
| `Backend/app.py` | Extracts actual code for Chapter 5 and Chapter 8 snippets; confirms API routes, thresholds, polling intervals, recovery_log logic |
| `Backend/requirements.txt` | Confirms exact dependency versions (Flask 3.1.3, flask-cors 5.0.0, boto3) |
| `Backend/demo_setup.py` | Extracts AWS resource creation sequence for Chapter 5 |
| `Backend/stress_demo.py` | Extracts SSM stress testing approach for Chapter 6 |
| `src/components/dashboard/*.tsx` | Confirms component names and polling patterns for Chapters 4, 5, 8 |
| `docs/project-overview.md` | High-level architecture and feature descriptions |
| `docs/backend-scripts-guide.md` | Script descriptions for Chapter 5 implementation section |

### Document Writer

The writer uses two operations:
- `fsWrite(path, content)` — creates the file with the first chunk (front matter through Abstract)
- `fsAppend(path, content)` — appends each subsequent chapter

Each append call covers one logical section (one chapter or one back-matter section) to keep individual write operations manageable.

### Content Sections (20 total)

The document is divided into 20 structural sections written in this order:

| # | Section | Target Length |
|---|---|---|
| 1 | Title Page | ~0.5 page |
| 2 | Bonafide Certificate | ~0.5 page |
| 3 | Declaration | ~0.5 page |
| 4 | Acknowledgement | ~1 page |
| 5 | Table of Contents | ~1 page |
| 6 | List of Figures | ~0.5 page |
| 7 | List of Abbreviations | ~1 page |
| 8 | Abstract | ~2 pages (600–800 words) |
| 9 | Chapter 1: Introduction | 10–12 pages |
| 10 | Chapter 2: Literature Survey | 10–12 pages |
| 11 | Chapter 3: Existing System | 6–8 pages |
| 12 | Chapter 4: Proposed System | 10–12 pages |
| 13 | Chapter 5: System Implementation | 12–15 pages |
| 14 | Chapter 6: System Testing | 6–8 pages |
| 15 | Chapter 7: Performance Analysis | 6–8 pages |
| 16 | Chapter 8: Sample Code | 8–10 pages |
| 17 | Chapter 9: Results and Discussion | 6–8 pages |
| 18 | Chapter 10: Conclusion | 5–6 pages |
| 19 | References | 2–3 pages |
| 20 | Appendix | 3–4 pages |

---

## Data Models

### Recovery Event (from app.py)

The `_log_event` function produces events with these fields, referenced throughout the dissertation:

```python
{
  "type": str,           # "High CPU Alert" | "Instance Down" | "Auto Recovery" | "Health Check"
  "status": str,         # "TRIGGERED" | "IN-PROGRESS" | "COMPLETED" | "HEALTHY"
  "message": str,        # Human-readable description
  "time": str,           # "%Y-%m-%d %H:%M"
  "instance_id": str,    # AWS instance ID
  "failure_reason": str, # Why the failure occurred
  "fix_applied": str,    # What action was taken
  "failure_type": str,   # "CRITICAL_CPU" | "HIGH_CPU" | "INSTANCE_DOWN" | "STATUS_CHECK"
  "action_taken": str,   # "REBOOT_INSTANCE" | "START_INSTANCE" | "MONITORING" | "NONE"
  "result": str,         # Outcome description
  "cpu_at_failure": float # CPU% at time of detection
}
```

### /api/recovery Response Shape

```json
{
  "events": [...],           // last 10 events from recovery_log
  "total_recoveries": 0,     // count of events with action_taken not in (None, "NONE", "MONITORING")
  "last_recovery_time": null // time string of most recent non-healthy event
}
```

### Failure Classification Table

| Failure_Type | Trigger Condition | Action_Taken |
|---|---|---|
| CRITICAL_CPU | CPU ≥ 90% | REBOOT_INSTANCE |
| HIGH_CPU | CPU > 70% and < 90% | REBOOT_INSTANCE |
| INSTANCE_DOWN | State in stopping/stopped/terminated | MONITORING → START_INSTANCE |
| STATUS_CHECK | CloudWatch status check alarm | MONITORING |
| HEALTHY | CPU ≤ 70%, state = running | NONE |

---

## Chapter Content Design

### Chapter 1: Introduction (10–12 pages)

Subsections:
- 1.1 Background and Context — evolution from physical servers to cloud-native; AWS market context
- 1.2 Importance of Cloud Computing — uptime requirements, SLA implications, cost of downtime
- 1.3 Problem Statement — undetected EC2 crashes, CPU runaway processes, manual DevOps burden
- 1.4 Objectives of the Project — 5+ numbered measurable goals referencing specific thresholds
- 1.5 Scope of the Project — what is and is not covered (single region, EC2 only, no RDS/ECS)
- 1.6 Motivation — real-world pain points that drove the design
- 1.7 Real-World Applications — e-commerce, banking, SaaS scenarios
- 1.8 Limitations of Current Approaches — manual console monitoring, alert fatigue, no auto-remediation

Required table: Manual vs Automated Recovery comparison (detection time, response time, human effort, reliability, cost).

### Chapter 2: Literature Survey (10–12 pages)

Eight systems covered with one paragraph each:
1. AWS Auto Scaling (native EC2 scaling, no CPU-based reboot healing)
2. Kubernetes self-healing (pod restart policies, liveness probes — container-level, not VM-level)
3. Netflix Chaos Monkey (fault injection, not remediation)
4. Prometheus + Grafana (monitoring/alerting, no auto-remediation)
5. Nagios (legacy monitoring, requires manual runbooks)
6. Zabbix (open-source APM, complex setup, no built-in healing)
7. Datadog (commercial APM, alerting only, no auto-remediation)
8. PagerDuty (incident management, human-in-the-loop)

Required table: Literature Survey Summary Table (Author/System, Year, Technology Used, Key Feature, Limitation) — 8+ rows.

Concluding subsection: Research Gap — none of the surveyed systems combine real-time CPU-based healing + instance state recovery + live dashboard + SNS alerting in a single lightweight stack.

### Chapter 3: Existing System (6–8 pages)

Three architectures described:
1. Manual AWS Console Monitoring — engineer watches CloudWatch dashboard, manually reboots
2. CloudWatch + SNS without auto-remediation — alarms fire emails but no automated action
3. Third-party APM tools (Datadog/New Relic) — rich monitoring but no built-in EC2 healing

Gap Analysis Table (8+ rows): Feature, Existing System Capability, Proposed System Capability — covering detection latency, auto-remediation, CPU-based healing, email alerting, dashboard visualisation, instance state tracking, recovery logging, cost.

Six drawbacks in paragraph form: detection latency, no auto-remediation, alert fatigue, high cost, complex setup, no unified dashboard.

### Chapter 4: Proposed System (10–12 pages)

ASCII architecture diagram showing all layers with directional arrows (React Frontend → Flask Backend → AWS services).

Six frontend component paragraphs: MetricCards, EC2StatusPanel, CPUUtilizationChart, CloudWatchAlarms, AutoScalingLogs, RecoveryEvents.

Backend module: Flask REST API (10 endpoints), Monitor_Thread (20s polling), SNS integration, recovery_log (50-event cap).

Cloud Infrastructure module: EC2, CloudWatch, Auto Scaling, SNS, IAM, Lambda, SSM — role of each.

Data Flow Diagram: text-based sequence from CPU spike → monitor detection → reboot → state transitions → recovery confirmation.

Five advantages: fully automated, zero-cost application layer, real-time visibility, dual-layer healing (Flask + Lambda), email alerting.

### Chapter 5: System Implementation (12–15 pages)

Tools and Technologies Table: Python 3, Flask 3.1.3, flask-cors 5.0.0, boto3, React 18, TypeScript, Vite, Tailwind CSS, Recharts, Framer Motion, shadcn-ui, Node.js, AWS CLI.

AWS setup sequence referencing demo_setup.py: SNS topic creation, IAM role, EC2 instance creation (4 instances tagged `Project: auto-recovery`), CloudWatch alarms, ASG creation.

Four required code snippets:
- (a) `_monitor_loop` core logic (state comparison + CPU check)
- (b) `get_cpu` function (CloudWatch get_metric_statistics call)
- (c) `/api/heal` endpoint
- (d) Frontend polling pattern (useEffect + setInterval at 30s)

Folder structure tree: Backend/, src/components/dashboard/, src/pages/, docs/, root config files.

Failure_Type classification table: CRITICAL_CPU, HIGH_CPU, INSTANCE_DOWN, STATUS_CHECK with trigger conditions and actions.

Lambda flow: CloudWatch Alarm → SNS Topic → Lambda Function → ec2.reboot_instances() → SNS email confirmation.

### Chapter 6: System Testing (6–8 pages)

Test Cases Table (12+ rows): Test Case ID, Test Description, Input/Precondition, Expected Output, Actual Output, Status.

Test cases cover: all 10 API endpoints, CPU threshold detection (70% and 90%), state transition logging, SNS email dispatch, manual heal trigger, dashboard data refresh, alarm state display, ASG activity display, recovery event ordering, CPU chart data rendering, error handling for missing instances, concurrent monitor thread safety.

Stress testing methodology: stress_demo.py and scenario_demo.py using SSM to spike CPU without SSH keys.

Instance termination test: scenario_demo.py terminate → recovery sequence in RecoveryEvents panel.

Two negative test cases: (a) no instances tagged `Project: auto-recovery`, (b) SNS topic does not exist at startup.

### Chapter 7: Performance Analysis (6–8 pages)

Performance Metrics Table: backend poll interval (20s), frontend refresh interval (30s), max recovery log size (50), CPU metric period (300s), CPU metric window (15 min current / 1h / 24h chart), API endpoint count (10).

MTTD/MTTR Comparison Table: proposed system vs manual monitoring across MTTD, MTTR, human effort, notification latency, cost.

Scalability discussion: tag-based instance discovery scales linearly; each additional instance adds one describe_instances result and one get_metric_statistics call per 20s cycle.

Cost efficiency: Flask backend and React frontend run locally (zero cloud hosting cost); only AWS API calls (CloudWatch, EC2, SNS) incur cost — typically < $1/month for a small fleet.

### Chapter 8: Sample Code (8–10 pages)

Complete `_monitor_loop` with annotations: EC2 describe_instances call, state comparison logic, SNS publish calls, CPU threshold check, 20-second sleep.

Complete `_log_event` with annotations: all 11 fields explained.

`/api/recovery` endpoint with response shape explanation: `{ events, total_recoveries, last_recovery_time }`.

`get_cpu` function with CloudWatch get_metric_statistics explanation, aligned time range calculation, datapoint sorting.

Frontend polling pattern: useEffect + setInterval at 30s from a dashboard component.

`demo_setup.py` AWS resource creation sequence as numbered list with code excerpts.

### Chapter 9: Results and Discussion (6–8 pages)

Six dashboard component output descriptions: what each shows and how it changes during a recovery event.

Auto-healing sequence as observed in RecoveryEvents panel: "High CPU Alert — TRIGGERED" → state transitions → "Auto Recovery — COMPLETED".

SNS email content format: instance name, CPU%, failure type, action, timestamp, dashboard URL.

Observed behaviour during scenario_demo.py terminate: running → stopping → stopped → pending → running.

Results Summary Table: Objective, Expected Outcome, Observed Outcome, Status — mapping Chapter 1 objectives to observed results.

### Chapter 10: Conclusion (5–6 pages)

Project summary: background thread monitoring, dual-layer healing, SNS alerting, React live dashboard.

Five known limitations: in-memory recovery_log (lost on restart), single-region (us-west-1 only), no persistent database, no authentication on API endpoints, polling-based detection latency.

Six future enhancements: persistent database for recovery logs, multi-region support, predictive scaling using ML, Kubernetes migration, role-based access control, WebSocket-based real-time push.

Concluding paragraph: 150+ words on academic and practical significance.

### References (20+ IEEE citations)

Covers: AWS official documentation (EC2, CloudWatch, SNS, Lambda, Auto Scaling, IAM, SSM), academic papers on cloud auto-scaling and self-healing, React, Flask, boto3, Recharts, Tailwind CSS, Framer Motion, NIST cloud computing definitions.

All online references include URL and access date.

### Appendix

API Reference Table (10 endpoints): Endpoint, Method, Description, Response Format.

AWS IAM policy permissions required.

Complete folder structure.

`requirements.txt` contents.

Optional: Publication abstract subsection.

---

## Writing Approach

### Academic Tone Rules

- All chapter body text in formal academic prose — complete paragraphs, not bullet lists (except where tables or code blocks are required)
- Past tense for describing what was implemented; present tense for describing what the system does
- No contractions, no first-person singular ("I"), no vague qualifiers ("very", "quite")
- Technical acronyms spelled out on first use: "Amazon Web Services (AWS)"
- Domain terminology consistent with the Glossary in requirements.md

### Structural Rules

- Every chapter heading: `# Chapter N: Title`
- Every section heading: `## N.M Section Title`
- Every subsection: `### N.M.P Subsection Title`
- At least one Markdown table per chapter (Chapters 1–10)
- All diagrams as ASCII/text with figure captions and explanatory paragraphs
- Code blocks with language identifiers: ` ```python `, ` ```typescript `, ` ```bash `

### Technical Accuracy Constraints

All of the following values must appear verbatim in the document:

| Fact | Value |
|---|---|
| AWS region | us-west-1 |
| Backend poll interval | 20 seconds |
| Frontend poll interval | 30 seconds |
| HIGH_CPU threshold | > 70% |
| CRITICAL_CPU threshold | ≥ 90% |
| recovery_log capacity | 50 events |
| /api/recovery returns | 10 most recent events |
| Flask version | 3.1.3 |
| flask-cors version | 5.0.0 |
| Dashboard components | MetricCards, EC2StatusPanel, CPUUtilizationChart, CloudWatchAlarms, AutoScalingLogs, RecoveryEvents |
| Backend scripts count | 11 |
| REST API endpoints | 10 |
| SNS topic name | CloudAutoRecoveryAlerts |
| EC2 discovery tag | Project: auto-recovery |

---

## File Output Strategy

The document is written in multiple operations to avoid single-write size limits:

1. `fsWrite('.kiro/specs/cloud-auto-recovery-dissertation/design.md', ...)` — this design document
2. `fsWrite('docs/dissertation.md', ...)` — Title Page through Abstract (front matter)
3. `fsAppend('docs/dissertation.md', ...)` — Chapter 1: Introduction
4. `fsAppend('docs/dissertation.md', ...)` — Chapter 2: Literature Survey
5. `fsAppend('docs/dissertation.md', ...)` — Chapter 3: Existing System
6. `fsAppend('docs/dissertation.md', ...)` — Chapter 4: Proposed System
7. `fsAppend('docs/dissertation.md', ...)` — Chapter 5: System Implementation
8. `fsAppend('docs/dissertation.md', ...)` — Chapter 6: System Testing
9. `fsAppend('docs/dissertation.md', ...)` — Chapter 7: Performance Analysis
10. `fsAppend('docs/dissertation.md', ...)` — Chapter 8: Sample Code
11. `fsAppend('docs/dissertation.md', ...)` — Chapter 9: Results and Discussion
12. `fsAppend('docs/dissertation.md', ...)` — Chapter 10: Conclusion
13. `fsAppend('docs/dissertation.md', ...)` — References
14. `fsAppend('docs/dissertation.md', ...)` — Appendix

No other files are created. The design document itself (`design.md`) is the only additional file produced during the design phase.

---

## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system — essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*

### Property 1: All Twenty Sections Present in Order

*For any* generated dissertation document, parsing the Markdown heading structure should yield all twenty required structural sections (Title Page, Bonafide Certificate, Declaration, Acknowledgement, Table of Contents, List of Figures, List of Abbreviations, Abstract, Chapter 1 through Chapter 10, References, Appendix) appearing in the specified order.

**Validates: Requirements 1.1**

### Property 2: Document Length Within Target Range

*For any* generated dissertation document, the total word count should fall within the range corresponding to 80–90 printed pages (approximately 24,000–31,500 words at 300–350 words per page).

**Validates: Requirements 1.2**

### Property 3: Hierarchical Section Numbering

*For any* chapter heading in the document, it should follow the pattern "Chapter N: Title"; and for any subsection heading, it should follow the hierarchical numbering pattern "N.M" or "N.M.P".

**Validates: Requirements 1.3**

### Property 4: Minimum Abbreviations Count

*For any* generated document, the List of Abbreviations section should contain at least 20 defined abbreviation entries.

**Validates: Requirements 1.6**

### Property 5: Acknowledgement Word Count

*For any* generated document, the Acknowledgement section should contain at least 200 words.

**Validates: Requirements 2.4**

### Property 6: Abstract Length Within Range

*For any* generated document, the Abstract section should contain between 600 and 800 words.

**Validates: Requirements 3.1**

### Property 7: Abstract Contains Required Technical Values

*For any* generated document, the Abstract section should contain all of the following specific technical values: "70%", "90%", "20 seconds", "30 seconds", "us-west-1", and "10" (in the context of REST API endpoints).

**Validates: Requirements 3.3**

### Property 8: Abstract Keywords Line

*For any* generated document, the Abstract section should contain a Keywords line listing at least 8 comma-separated domain-relevant terms.

**Validates: Requirements 3.4**

### Property 9: Chapter 1 Required Subsections Present

*For any* generated document, Chapter 1 should contain headings for all required subsections: Background, Problem Statement, Objectives, Scope, Motivation, Real-World Applications, and Limitations.

**Validates: Requirements 4.1**

### Property 10: At Least One Table Per Chapter

*For any* chapter in Chapters 1 through 10 of the generated document, that chapter should contain at least one Markdown pipe-delimited table.

**Validates: Requirements 16.6**

### Property 11: Literature Survey References Eight Systems

*For any* generated document, Chapter 2 should reference at least eight distinct existing systems or research works by name.

**Validates: Requirements 5.2**

### Property 12: Gap Analysis Table Row Count

*For any* generated document, the Gap Analysis Table in Chapter 3 should contain at least eight data rows.

**Validates: Requirements 6.3**

### Property 13: Chapter 4 Describes All Six Dashboard Components

*For any* generated document, Chapter 4 should contain all six dashboard component names: MetricCards, EC2StatusPanel, CPUUtilizationChart, CloudWatchAlarms, AutoScalingLogs, and RecoveryEvents.

**Validates: Requirements 7.3**

### Property 14: Chapter 5 Code Snippet Count

*For any* generated document, Chapter 5 should contain at least four fenced code blocks.

**Validates: Requirements 8.4**

### Property 15: Test Cases Table Row Count

*For any* generated document, the Test Cases Table in Chapter 6 should contain at least 12 data rows.

**Validates: Requirements 9.2**

### Property 16: Chapter 10 Completeness

*For any* generated document, Chapter 10 should list at least five known limitations and at least six future enhancement proposals.

**Validates: Requirements 13.3, 13.4**

### Property 17: References Count

*For any* generated document, the References section should contain at least 20 IEEE-formatted citation entries.

**Validates: Requirements 14.1**

### Property 18: API Reference Table Completeness

*For any* generated document, the API Reference Table in the Appendix should contain all 10 endpoint paths: `/api/instances`, `/api/summary`, `/api/alarms`, `/api/recovery`, `/api/cpu-metrics`, `/api/heal`, `/api/scaling`, `/api/sns/setup`, `/api/sns/status`, `/api/sns/subscribe`.

**Validates: Requirements 15.2**

### Property 19: Technical Constants Accuracy

*For any* generated document, all of the following technical constants should appear with their correct values: Flask version 3.1.3, flask-cors version 5.0.0, AWS region us-west-1, backend poll interval 20 seconds, frontend poll interval 30 seconds, HIGH_CPU threshold 70%, CRITICAL_CPU threshold 90%, recovery_log capacity 50 events, SNS topic name CloudAutoRecoveryAlerts, EC2 discovery tag "Project: auto-recovery", 11 backend scripts, 10 REST API endpoints.

**Validates: Requirements 17.1, 17.2, 17.3, 17.4, 17.5, 17.6, 17.7, 17.9, 17.10**

### Property 20: Valid Markdown Structure

*For any* generated document, parsing the file with a standard Markdown parser should produce a valid document tree with no unclosed fenced code blocks, no malformed table rows, and no broken heading hierarchy.

**Validates: Requirements 18.2**

---

## Error Handling

### Missing Source Files

If any source file cannot be read (e.g., `Backend/app.py` is missing), the generator should note the gap in the relevant chapter and use the values from the requirements document as the authoritative source of truth. The document should not be left incomplete.

### Write Operation Failures

If an `fsAppend` call fails mid-generation, the generator should retry the failed section. Since each append covers one chapter, a failure does not corrupt previously written content.

### Content Length Estimation

If a chapter section is running short of its target page count, the generator should expand explanatory paragraphs, add additional context, or include supplementary tables rather than padding with repetitive content.

---

## Testing Strategy

### Unit Tests

Unit tests verify specific structural properties of the generated document:

- Verify the file exists at `docs/dissertation.md`
- Verify the document begins with the correct level-1 heading
- Verify all 20 section headings are present
- Verify the Abstract section word count is in [600, 800]
- Verify the References section contains ≥ 20 entries
- Verify the API Reference Table contains all 10 endpoint paths
- Verify no fenced code blocks are unclosed

Unit tests focus on concrete, deterministic checks that do not require generating the full document.

### Property-Based Tests

Property-based tests verify universal structural properties using a Markdown parsing library (e.g., `markdown-it` for Node.js or `mistune` for Python) combined with a property-based testing library (e.g., `hypothesis` for Python or `fast-check` for TypeScript).

Each property test runs a minimum of 100 iterations over randomly sampled sections of the document to verify structural invariants hold throughout.

**Tag format: Feature: cloud-auto-recovery-dissertation, Property {N}: {property_text}**

Property tests to implement:

- **Property 1**: Parse heading structure → verify 20 sections in order
  `# Feature: cloud-auto-recovery-dissertation, Property 1: all-twenty-sections-present-in-order`

- **Property 10**: For each chapter 1–10, count tables → verify ≥ 1
  `# Feature: cloud-auto-recovery-dissertation, Property 10: at-least-one-table-per-chapter`

- **Property 19**: For each required technical constant, search document → verify correct value present
  `# Feature: cloud-auto-recovery-dissertation, Property 19: technical-constants-accuracy`

- **Property 20**: Parse full document with Markdown parser → verify no structural errors
  `# Feature: cloud-auto-recovery-dissertation, Property 20: valid-markdown-structure`

### Dual Testing Rationale

Unit tests catch concrete bugs (wrong file path, missing section, wrong version number). Property tests verify that structural invariants hold across the entire document regardless of which section is being examined. Together they provide comprehensive coverage: unit tests handle specific known cases, property tests handle the general correctness of the document structure.
