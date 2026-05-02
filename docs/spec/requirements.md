# Requirements Document

## Introduction

This specification defines the requirements for generating a full university-style dissertation document (80–90 pages) titled **"Cloud Infrastructure Auto-Recovery Dashboard: An Intelligent Self-Healing System for AWS EC2 Instances"**. The dissertation documents a completed full-stack project that monitors AWS EC2 instances in real time, automatically detects failures, and heals them without manual intervention. The output is a single comprehensive Markdown file saved to the repository, structured as a formal BCA/B.Tech/MCA final-year project submission.

The Dissertation_Generator is the system responsible for producing this document. It must generate all twenty sections in sequence, maintain academic tone throughout, embed accurate technical content derived from the actual codebase, and meet the page-count and quality standards of a university submission.

---

## Glossary

- **Dissertation_Generator**: The system (AI agent or process) responsible for authoring and writing the full dissertation document.
- **Document**: The output Markdown file containing the complete dissertation.
- **EC2**: Amazon Elastic Compute Cloud — virtual server instances managed by AWS.
- **Flask_Backend**: The Python Flask application (`app.py`) that serves REST API endpoints and runs the background health monitor.
- **React_Frontend**: The TypeScript/React/Vite single-page application that renders the live dashboard at `http://localhost:5173`.
- **Monitor_Thread**: The background Python thread (`_monitor_loop`) inside `app.py` that polls EC2 every 20 seconds.
- **SNS**: Amazon Simple Notification Service — used to send email alerts for recovery events.
- **CloudWatch**: AWS monitoring service used for CPU and status-check alarms.
- **Auto_Scaling_Group**: AWS ASG that automatically replaces terminated instances.
- **Lambda_Function**: Optional serverless function (`CloudAutoRecoveryFunction`) deployed via `setup_lambda.py` for a second healing layer.
- **SSM**: AWS Systems Manager — used by `stress_demo.py` to run remote commands without SSH keys.
- **Recovery_Event**: A structured log entry capturing failure type, action taken, CPU at failure, and result.
- **Failure_Type**: Classification of a detected failure — one of `CRITICAL_CPU`, `HIGH_CPU`, `INSTANCE_DOWN`, `STATUS_CHECK`, or `HEALTHY`.
- **EARS**: Easy Approach to Requirements Syntax — the pattern language used for all acceptance criteria.
- **INCOSE**: International Council on Systems Engineering — quality rules applied to all requirements.
- **Chapter**: A top-level numbered section of the dissertation document.
- **Section**: A subsection within a chapter.

---

## Requirements

### Requirement 1: Document Structure and Completeness

**User Story:** As a university student, I want the dissertation to contain all required front matter and chapters in the correct order, so that the submission meets the formal structure expected by the examining committee.

#### Acceptance Criteria

1. THE Dissertation_Generator SHALL produce a Document containing all twenty structural sections in the following order: Title Page, Bonafide Certificate, Declaration, Acknowledgement, Table of Contents, List of Figures, List of Abbreviations, Abstract, Chapter 1 through Chapter 10, References, and Appendix.
2. THE Dissertation_Generator SHALL produce a Document whose total content is equivalent to 80–90 printed pages when rendered at standard academic formatting (12pt font, 1.5 line spacing, A4 page).
3. WHEN the Document is rendered, THE Dissertation_Generator SHALL ensure each Chapter heading is numbered (e.g., "Chapter 1: Introduction") and each subsection is numbered hierarchically (e.g., "1.1", "1.2.3").
4. THE Dissertation_Generator SHALL include a Table of Contents that lists every chapter and major subsection with its corresponding section number.
5. THE Dissertation_Generator SHALL include a List of Figures that enumerates every figure reference in the Document with a descriptive caption.
6. THE Dissertation_Generator SHALL include a List of Abbreviations that defines every technical acronym used in the Document (minimum 20 abbreviations).

---

### Requirement 2: Front Matter Quality

**User Story:** As a student submitting a dissertation, I want the front matter pages to be properly formatted and contain all required institutional and personal declarations, so that the document is accepted as a valid university submission.

#### Acceptance Criteria

1. THE Dissertation_Generator SHALL produce a Title Page containing: project title, student name placeholder, registration number placeholder, institution name placeholder, department name, degree name, academic year, and supervisor name placeholder.
2. THE Dissertation_Generator SHALL produce a Bonafide Certificate containing a formal declaration by the institution that the work is original, with placeholders for supervisor signature, head of department signature, and date.
3. THE Dissertation_Generator SHALL produce a Declaration page containing a student statement that the work is original, has not been submitted elsewhere, and lists all sources used, with a placeholder for student signature and date.
4. THE Dissertation_Generator SHALL produce an Acknowledgement page of at least 200 words that thanks supervisors, institution, AWS documentation, and open-source communities in formal academic language.
5. IF any front matter section is missing, THEN THE Dissertation_Generator SHALL halt and report which section is absent before producing any output.

---

### Requirement 3: Abstract Requirements

**User Story:** As a reader of the dissertation, I want a detailed abstract that summarises the entire project, so that I can understand the problem, approach, and outcomes without reading the full document.

#### Acceptance Criteria

1. THE Dissertation_Generator SHALL produce an Abstract of 600–800 words covering: problem statement, proposed solution, technology stack, key features, implementation approach, testing methodology, and results.
2. THE Dissertation_Generator SHALL write the Abstract in past tense, third person, academic prose — not bullet points.
3. THE Dissertation_Generator SHALL include in the Abstract: the specific CPU threshold values (70% and 90%), the polling intervals (20 seconds for backend, 30 seconds for frontend), the AWS region (us-west-1), and the number of REST API endpoints (10).
4. THE Dissertation_Generator SHALL include a Keywords line at the end of the Abstract listing at least 8 domain-relevant terms (e.g., "Cloud Computing, AWS EC2, Auto-Recovery, Self-Healing Systems, Flask, React, CloudWatch, SNS").

---

### Requirement 4: Chapter 1 — Introduction

**User Story:** As an examiner, I want Chapter 1 to establish the research context and motivation thoroughly, so that I can assess the student's understanding of the problem domain.

#### Acceptance Criteria

1. THE Dissertation_Generator SHALL produce Chapter 1 of 10–12 pages covering all of the following subsections: Background and Context, Importance of Cloud Computing, Problem Statement, Objectives of the Project, Scope of the Project, Motivation, Real-World Applications, and Limitations of Current Approaches.
2. THE Dissertation_Generator SHALL write the Background subsection explaining the evolution of cloud computing from physical servers to virtualisation to cloud-native infrastructure, referencing the shift from on-premises to AWS-hosted workloads.
3. THE Dissertation_Generator SHALL write the Problem Statement subsection explaining the specific failure modes addressed: undetected EC2 instance crashes, CPU runaway processes, and the manual intervention burden on DevOps engineers.
4. THE Dissertation_Generator SHALL list at least five numbered project objectives in the Objectives subsection, each written as a measurable goal (e.g., "To implement automated CPU-based healing that reboots instances within 20 seconds of threshold breach").
5. THE Dissertation_Generator SHALL include at least one comparison table in Chapter 1 contrasting manual recovery approaches with the proposed automated system across dimensions such as detection time, response time, human effort, and reliability.
6. THE Dissertation_Generator SHALL write the Real-World Applications subsection with at least three concrete industry scenarios (e.g., e-commerce platforms, banking systems, SaaS applications) where the system would provide value.

---

### Requirement 5: Chapter 2 — Literature Survey

**User Story:** As an examiner, I want Chapter 2 to demonstrate awareness of existing research and related systems, so that I can assess the student's academic grounding.

#### Acceptance Criteria

1. THE Dissertation_Generator SHALL produce Chapter 2 of 10–12 pages covering: existing research on cloud auto-scaling and self-healing systems, comparison of existing commercial and open-source monitoring tools, technologies used in similar systems, identified limitations of existing approaches, and a summary comparison table.
2. THE Dissertation_Generator SHALL reference at least eight distinct existing systems or research works (e.g., AWS Auto Scaling, Kubernetes self-healing, Netflix Chaos Monkey, Prometheus/Grafana, Nagios, Zabbix, Datadog, PagerDuty) with a paragraph of description for each.
3. THE Dissertation_Generator SHALL include a Literature Survey Summary Table with columns: Author/System, Year, Technology Used, Key Feature, Limitation — containing at least eight rows.
4. THE Dissertation_Generator SHALL write a concluding subsection identifying the research gap that the proposed system addresses, referencing specific limitations found in the surveyed systems.
5. WHEN describing existing systems, THE Dissertation_Generator SHALL write in academic prose with at least one full paragraph per system — not bullet-point lists.

---

### Requirement 6: Chapter 3 — Existing System

**User Story:** As an examiner, I want Chapter 3 to clearly describe the current state of practice and its shortcomings, so that the need for the proposed system is well justified.

#### Acceptance Criteria

1. THE Dissertation_Generator SHALL produce Chapter 3 of 6–8 pages covering: description of current manual and semi-automated cloud monitoring approaches, architecture of a typical existing system, drawbacks of existing systems, and a gap analysis table.
2. THE Dissertation_Generator SHALL describe at least three distinct existing system architectures (e.g., manual AWS Console monitoring, CloudWatch + SNS without auto-remediation, third-party APM tools) with a paragraph each.
3. THE Dissertation_Generator SHALL include a Gap Analysis Table with columns: Feature, Existing System Capability, Proposed System Capability — containing at least eight rows covering features such as detection latency, auto-remediation, CPU-based healing, email alerting, and dashboard visualisation.
4. THE Dissertation_Generator SHALL list at least six specific drawbacks of existing systems in paragraph form, not as a bare bullet list.

---

### Requirement 7: Chapter 4 — Proposed System

**User Story:** As an examiner, I want Chapter 4 to present the proposed system's architecture and design in sufficient detail, so that I can evaluate the technical soundness of the solution.

#### Acceptance Criteria

1. THE Dissertation_Generator SHALL produce Chapter 4 of 10–12 pages covering: system overview, system architecture, module descriptions (Frontend Module, Backend Module, Cloud Infrastructure Module), data flow description, and advantages of the proposed system.
2. THE Dissertation_Generator SHALL describe the system architecture using an ASCII or text-based diagram showing the React Frontend, Flask Backend, AWS EC2, CloudWatch, SNS, Auto Scaling Group, Lambda, and SSM layers with directional arrows indicating data flow.
3. THE Dissertation_Generator SHALL describe the Frontend Module covering all six dashboard components: MetricCards, EC2StatusPanel, CPUUtilizationChart, CloudWatchAlarms, AutoScalingLogs, and RecoveryEvents — with a paragraph for each.
4. THE Dissertation_Generator SHALL describe the Backend Module covering: the Flask REST API, the Monitor_Thread polling mechanism (20-second interval), the SNS integration, and the in-memory recovery_log (capped at 50 events).
5. THE Dissertation_Generator SHALL describe the Cloud Infrastructure Module covering all seven AWS services used: EC2, CloudWatch, Auto Scaling, SNS, IAM, Lambda, and SSM — with their specific roles in the system.
6. THE Dissertation_Generator SHALL include a Data Flow Diagram described in text showing the complete auto-healing sequence from CPU spike detection through reboot to recovery confirmation.
7. THE Dissertation_Generator SHALL list at least five advantages of the proposed system over existing approaches in paragraph form.

---

### Requirement 8: Chapter 5 — System Implementation

**User Story:** As a developer or examiner, I want Chapter 5 to document the complete implementation process with sufficient technical detail, so that the system could be reproduced from this chapter alone.

#### Acceptance Criteria

1. THE Dissertation_Generator SHALL produce Chapter 5 of 12–15 pages covering: development environment setup, tools and technologies with version numbers, step-by-step AWS resource provisioning, backend implementation details, frontend implementation details, deployment procedure, and folder structure.
2. THE Dissertation_Generator SHALL include a Tools and Technologies Table with columns: Tool/Technology, Version, Purpose — listing at minimum: Python 3, Flask 3.1.3, flask-cors 5.0.0, boto3, React 18, TypeScript, Vite, Tailwind CSS, Recharts, Framer Motion, shadcn-ui, Node.js, AWS CLI.
3. THE Dissertation_Generator SHALL describe the AWS setup sequence referencing the actual scripts: `demo_setup.py` (EC2 instances, CloudWatch alarms, ASG, SNS, IAM), `setup_lambda.py` (Lambda deployment), and the tag-based resource discovery pattern (`Project: auto-recovery`).
4. THE Dissertation_Generator SHALL include at least four code snippets from the actual codebase, each preceded by a description and followed by an explanation. Required snippets: (a) the `_monitor_loop` function core logic, (b) the `get_cpu` function, (c) the `/api/heal` endpoint, (d) a frontend component polling pattern.
5. THE Dissertation_Generator SHALL include the project folder structure as a formatted tree showing all major directories and files: `Backend/`, `src/components/dashboard/`, `src/pages/`, `docs/`, and root config files.
6. THE Dissertation_Generator SHALL describe the Failure_Type classification logic (CRITICAL_CPU, HIGH_CPU, INSTANCE_DOWN, STATUS_CHECK) and the Action_Taken values (REBOOT_INSTANCE, START_INSTANCE, MONITORING, NONE) in a table.
7. THE Dissertation_Generator SHALL describe the Lambda auto-healing flow: CloudWatch Alarm → SNS Topic → Lambda Function → `ec2.reboot_instances()` → SNS email confirmation.

---

### Requirement 9: Chapter 6 — System Testing

**User Story:** As an examiner, I want Chapter 6 to demonstrate that the system was rigorously tested, so that I can assess the reliability and correctness of the implementation.

#### Acceptance Criteria

1. THE Dissertation_Generator SHALL produce Chapter 6 of 6–8 pages covering: unit testing approach, integration testing approach, functional testing approach, load/stress testing approach, and a test cases table.
2. THE Dissertation_Generator SHALL include a Test Cases Table with columns: Test Case ID, Test Description, Input/Precondition, Expected Output, Actual Output, Status — containing at least 12 rows covering: API endpoint responses, CPU threshold detection, state transition logging, SNS email dispatch, manual heal trigger, dashboard data refresh, alarm state display, ASG activity display, recovery event ordering, CPU chart data rendering, error handling for missing instances, and concurrent monitor thread safety.
3. THE Dissertation_Generator SHALL describe the stress testing methodology using `stress_demo.py` and `scenario_demo.py`, explaining how SSM was used to spike CPU without SSH keys.
4. THE Dissertation_Generator SHALL describe the instance termination test using `scenario_demo.py terminate` and the expected recovery sequence logged in the RecoveryEvents panel.
5. THE Dissertation_Generator SHALL describe at least two negative test cases: (a) behaviour when no EC2 instances are tagged with `Project: auto-recovery`, and (b) behaviour when the SNS topic does not exist at startup.

---

### Requirement 10: Chapter 7 — Performance Analysis

**User Story:** As an examiner, I want Chapter 7 to provide quantitative analysis of the system's performance characteristics, so that I can evaluate whether the system meets production-grade standards.

#### Acceptance Criteria

1. THE Dissertation_Generator SHALL produce Chapter 7 of 6–8 pages covering: API response time analysis, detection latency analysis, recovery time analysis, scalability analysis, cost efficiency analysis, and a comparison table with traditional systems.
2. THE Dissertation_Generator SHALL include a Performance Metrics Table with columns: Metric, Value, Notes — covering: backend poll interval (20s), frontend refresh interval (30s), maximum recovery log size (50 events), CPU metric period (300s / 5 min), CPU metric window (15 min for current, 1h/24h for chart), API endpoints count (10).
3. THE Dissertation_Generator SHALL include a Comparison Table contrasting the proposed system against manual monitoring across dimensions: Mean Time to Detect (MTTD), Mean Time to Recover (MTTR), Human Effort Required, Notification Latency, and Cost.
4. THE Dissertation_Generator SHALL discuss the scalability characteristics of the tag-based instance discovery approach and its behaviour as the number of monitored instances grows.
5. THE Dissertation_Generator SHALL discuss the cost efficiency of the system, noting that the Flask backend and React frontend run locally (zero cloud hosting cost for the application layer) while only AWS service API calls incur cost.

---

### Requirement 11: Chapter 8 — Sample Code

**User Story:** As a technical examiner, I want Chapter 8 to present the most important code modules with explanations, so that I can assess the quality and correctness of the implementation.

#### Acceptance Criteria

1. THE Dissertation_Generator SHALL produce Chapter 8 of 8–10 pages presenting key code modules with line-by-line or block-by-block explanations.
2. THE Dissertation_Generator SHALL include the complete `_monitor_loop` function with annotations explaining: the EC2 describe_instances call, state comparison logic, SNS publish calls, CPU threshold check, and the 20-second sleep.
3. THE Dissertation_Generator SHALL include the complete `_log_event` function with annotations explaining all eight fields: type, status, message, time, instance_id, failure_reason, fix_applied, failure_type, action_taken, result, cpu_at_failure.
4. THE Dissertation_Generator SHALL include the `/api/recovery` endpoint implementation with explanation of the response shape: `{ events, total_recoveries, last_recovery_time }`.
5. THE Dissertation_Generator SHALL include the `get_cpu` function with explanation of the CloudWatch `get_metric_statistics` call, the aligned time range calculation, and the datapoint sorting logic.
6. THE Dissertation_Generator SHALL include at least one frontend code snippet showing the React polling pattern (useEffect + setInterval at 30-second intervals) from the dashboard components.
7. THE Dissertation_Generator SHALL include the `demo_setup.py` AWS resource creation sequence as a numbered list with code excerpts showing EC2 instance creation, CloudWatch alarm creation, and SNS topic setup.

---

### Requirement 12: Chapter 9 — Results and Discussion

**User Story:** As an examiner, I want Chapter 9 to present the observed outputs and discuss their significance, so that I can assess whether the system achieved its stated objectives.

#### Acceptance Criteria

1. THE Dissertation_Generator SHALL produce Chapter 9 of 6–8 pages covering: dashboard output descriptions, recovery event log observations, CPU chart observations, alarm state observations, SNS email delivery observations, and user experience discussion.
2. THE Dissertation_Generator SHALL describe each of the six dashboard components' visual output in detail, explaining what data is displayed and how it changes during a recovery event.
3. THE Dissertation_Generator SHALL describe the complete auto-healing sequence as observed in the RecoveryEvents panel, listing the exact event types and statuses in order: "High CPU Alert — TRIGGERED", state transitions logged, "Auto Recovery — COMPLETED".
4. THE Dissertation_Generator SHALL describe the SNS email content format, referencing the actual message template used in `app.py` (instance name, CPU%, failure type, action, timestamp, dashboard URL).
5. THE Dissertation_Generator SHALL discuss the observed behaviour of the system during the `scenario_demo.py terminate` test, describing the state transition sequence: running → stopping → stopped → pending → running.
6. THE Dissertation_Generator SHALL include a Results Summary Table with columns: Objective, Expected Outcome, Observed Outcome, Status — mapping each of the Chapter 1 objectives to its observed result.

---

### Requirement 13: Chapter 10 — Conclusion and Future Enhancement

**User Story:** As an examiner, I want Chapter 10 to summarise the project's contributions and propose credible future work, so that I can assess the student's critical reflection and forward thinking.

#### Acceptance Criteria

1. THE Dissertation_Generator SHALL produce Chapter 10 of 5–6 pages covering: project summary, achievement of objectives, known limitations, and future enhancement proposals.
2. THE Dissertation_Generator SHALL summarise the project's key contributions in paragraph form, referencing the specific technical achievements: background thread monitoring, dual-layer healing (Flask + Lambda), SNS alerting, and the React live dashboard.
3. THE Dissertation_Generator SHALL list at least five known limitations of the current system in paragraph form, including: in-memory recovery_log (lost on restart), single-region deployment (us-west-1 only), no persistent database, no authentication on API endpoints, and polling-based detection latency.
4. THE Dissertation_Generator SHALL propose at least six future enhancements with a paragraph each, including: persistent database for recovery logs, multi-region support, predictive scaling using ML, Kubernetes migration, role-based access control for the dashboard, and WebSocket-based real-time push instead of polling.
5. THE Dissertation_Generator SHALL write a concluding paragraph of at least 150 words that reflects on the project's academic and practical significance.

---

### Requirement 14: References Section

**User Story:** As an examiner, I want the References section to cite all sources used in the dissertation in a consistent academic format, so that the work's academic integrity can be verified.

#### Acceptance Criteria

1. THE Dissertation_Generator SHALL produce a References section of 2–3 pages containing at least 20 references.
2. THE Dissertation_Generator SHALL format all references in IEEE citation style: [N] Author(s), "Title," Source, Year.
3. THE Dissertation_Generator SHALL include references covering: AWS official documentation (EC2, CloudWatch, SNS, Lambda, Auto Scaling, IAM, SSM), academic papers on cloud auto-scaling and self-healing systems, references for React, Flask, boto3, Recharts, Tailwind CSS, and Framer Motion, and references for NIST cloud computing definitions.
4. IF a reference is to an online resource, THEN THE Dissertation_Generator SHALL include the URL and access date in the citation.

---

### Requirement 15: Appendix Section

**User Story:** As a reader, I want the Appendix to contain supplementary technical material that supports the main chapters without interrupting the narrative flow.

#### Acceptance Criteria

1. THE Dissertation_Generator SHALL produce an Appendix section containing at minimum: the complete list of REST API endpoints with request/response schemas, the AWS IAM policy permissions required by the system, the complete folder structure of the project, and the `requirements.txt` contents.
2. THE Dissertation_Generator SHALL include an API Reference Table in the Appendix with columns: Endpoint, Method, Description, Response Format — covering all 10 endpoints: `/api/instances`, `/api/summary`, `/api/alarms`, `/api/recovery`, `/api/cpu-metrics`, `/api/heal`, `/api/scaling`, `/api/sns/setup`, `/api/sns/status`, `/api/sns/subscribe`.
3. WHERE a publication or conference paper abstract is available, THE Dissertation_Generator SHALL include it in the Appendix as a separate subsection titled "Publication."

---

### Requirement 16: Writing Style and Academic Tone

**User Story:** As an examiner, I want the entire dissertation to be written in consistent academic English, so that it meets the language standards of a university submission.

#### Acceptance Criteria

1. THE Dissertation_Generator SHALL write all chapter body text in formal academic prose — complete paragraphs, not bullet-point lists — except where tables or code blocks are explicitly required.
2. THE Dissertation_Generator SHALL use past tense for describing what was implemented and present tense for describing what the system does.
3. THE Dissertation_Generator SHALL avoid informal language, contractions, first-person singular ("I"), and vague qualifiers ("very", "quite", "a lot").
4. THE Dissertation_Generator SHALL use domain-specific technical terminology consistently as defined in the Glossary.
5. WHEN introducing a technical acronym for the first time, THE Dissertation_Generator SHALL spell it out in full followed by the acronym in parentheses (e.g., "Amazon Web Services (AWS)").
6. THE Dissertation_Generator SHALL include at least one table per chapter (Chapters 1–10) to present comparative, structured, or quantitative information.
7. THE Dissertation_Generator SHALL describe all diagrams and figures in surrounding text — since images cannot be embedded, every architectural diagram SHALL be represented as an ASCII/text diagram with a figure caption and a full paragraph of explanation.

---

### Requirement 17: Technical Accuracy

**User Story:** As a technical examiner, I want all technical claims in the dissertation to be accurate and consistent with the actual codebase, so that the document faithfully represents the implemented system.

#### Acceptance Criteria

1. THE Dissertation_Generator SHALL use only the technology versions present in the actual project: Flask 3.1.3, flask-cors 5.0.0, boto3 (latest), React with TypeScript, Vite, Tailwind CSS, Recharts, Framer Motion, shadcn-ui.
2. THE Dissertation_Generator SHALL state the correct AWS region throughout: us-west-1.
3. THE Dissertation_Generator SHALL state the correct polling intervals: Monitor_Thread polls EC2 every 20 seconds; React_Frontend polls Flask API every 30 seconds.
4. THE Dissertation_Generator SHALL state the correct CPU thresholds: HIGH_CPU at >70%, CRITICAL_CPU at ≥90%.
5. THE Dissertation_Generator SHALL state the correct recovery_log capacity: capped at 50 events (most recent first), with the `/api/recovery` endpoint returning the 10 most recent.
6. THE Dissertation_Generator SHALL state the correct number and names of dashboard components: MetricCards, EC2StatusPanel, CPUUtilizationChart, CloudWatchAlarms, AutoScalingLogs, RecoveryEvents.
7. THE Dissertation_Generator SHALL state the correct number of backend utility scripts: 11 scripts (app.py, demo_setup.py, setup_lambda.py, start_demo.py, stop_demo.py, stress_demo.py, scenario_demo.py, status_demo.py, diagnose_sns.py, fix_sns_email.py, terminate_old.py).
8. WHEN describing the `/api/recovery` response, THE Dissertation_Generator SHALL use the correct shape: `{ events: [...], total_recoveries: number, last_recovery_time: string | null }`.
9. THE Dissertation_Generator SHALL correctly describe the SNS topic name as `CloudAutoRecoveryAlerts`.
10. THE Dissertation_Generator SHALL correctly describe the EC2 instance tag used for discovery as `Project: auto-recovery`.

---

### Requirement 18: Document Output and File Placement

**User Story:** As a developer, I want the dissertation to be saved as a single Markdown file in the repository, so that it can be version-controlled and rendered by any Markdown viewer.

#### Acceptance Criteria

1. THE Dissertation_Generator SHALL save the Document as a single Markdown file at the path `docs/dissertation.md` within the project repository.
2. THE Dissertation_Generator SHALL use standard Markdown syntax: `#` for chapter headings, `##` for section headings, `###` for subsection headings, fenced code blocks with language identifiers, and pipe-delimited tables.
3. THE Dissertation_Generator SHALL begin the Document with a level-1 heading containing the full project title.
4. IF the Document exceeds the capacity of a single write operation, THEN THE Dissertation_Generator SHALL use append operations to complete the file without overwriting previously written content.
5. THE Dissertation_Generator SHALL NOT create any additional summary, README, or process documentation files beyond `docs/dissertation.md`.

---

### Requirement 19: Correctness Properties for Document Validation

**User Story:** As a quality reviewer, I want the generated document to satisfy verifiable correctness properties, so that automated or manual checks can confirm the document meets all structural and content requirements.

#### Acceptance Criteria

1. THE Dissertation_Generator SHALL produce a Document such that parsing the Markdown heading structure yields exactly 10 chapter headings numbered Chapter 1 through Chapter 10, plus the required front matter and back matter sections.
2. THE Dissertation_Generator SHALL produce a Document such that every term listed in the List of Abbreviations appears at least once in the body text of the Document (round-trip property: abbreviation list ↔ body usage).
3. THE Dissertation_Generator SHALL produce a Document such that every figure caption listed in the List of Figures corresponds to a figure reference in the body text (round-trip property: figure list ↔ figure reference).
4. THE Dissertation_Generator SHALL produce a Document such that every objective stated in Chapter 1 is addressed in the Results Summary Table in Chapter 9 (round-trip property: objectives ↔ results).
5. THE Dissertation_Generator SHALL produce a Document such that all technical values stated (CPU thresholds, polling intervals, log capacity, endpoint count, script count) are consistent across all chapters — no chapter SHALL contradict another on these values (invariant: technical facts are globally consistent).
6. WHEN the Document is complete, THE Dissertation_Generator SHALL verify that the References section contains at least 20 entries and that each entry follows IEEE format (invariant: reference count ≥ 20).
7. THE Dissertation_Generator SHALL produce a Document such that the total word count of all chapter body text (excluding tables, code blocks, and headings) is at least 18,000 words (invariant: minimum prose density for 80-page equivalence).

---

### Requirement 20: Error Handling During Generation

**User Story:** As a developer running the generation process, I want the system to handle partial failures gracefully, so that a recoverable error in one chapter does not prevent the rest of the document from being generated.

#### Acceptance Criteria

1. IF the Dissertation_Generator encounters an error while writing a specific chapter, THEN THE Dissertation_Generator SHALL log the error, skip to the next chapter, and complete the remaining chapters before reporting the failure.
2. IF the output file already exists at `docs/dissertation.md`, THEN THE Dissertation_Generator SHALL overwrite it with the new Document rather than appending to stale content.
3. THE Dissertation_Generator SHALL produce a Document where every chapter section is non-empty — no chapter SHALL consist solely of a heading with no body content.
