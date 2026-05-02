# Implementation Plan: Cloud Auto-Recovery Dissertation

## Overview

Generate `docs/dissertation.md` — a full 80–90 page university-style dissertation — by reading the actual codebase and writing the document sequentially using `fsWrite` (front matter) followed by `fsAppend` (one call per chapter/section). Each task maps to one write or append operation. Tasks must be executed in order since each append depends on the file existing from the previous step.

## Tasks

- [ ] 1. Read source files before writing
  - Read `Backend/app.py` to extract `_monitor_loop`, `_log_event`, `get_cpu`, `/api/heal`, `/api/recovery` implementations
  - Read `Backend/demo_setup.py` to extract AWS resource creation sequence
  - Read `Backend/stress_demo.py` and `Backend/scenario_demo.py` for testing methodology
  - Read all `src/components/dashboard/*.tsx` files to confirm component names and polling patterns
  - Read `docs/project-overview.md` and `docs/backend-scripts-guide.md` for architecture context
  - Read `Backend/requirements.txt` to confirm exact dependency versions
  - _Requirements: 17.1, 17.2, 17.3, 17.4, 17.5, 17.6, 17.7_

- [ ] 2. Create `docs/dissertation.md` with front matter (Title Page through Abstract)
  - Use `fsWrite('docs/dissertation.md', ...)` to create the file
  - Write Title Page: project title, student name placeholder, registration number placeholder, institution name placeholder, department, degree, academic year, supervisor placeholder
  - Write Bonafide Certificate with supervisor signature placeholder, HoD signature placeholder, date placeholder
  - Write Declaration page with student signature placeholder and date placeholder
  - Write Acknowledgement of at least 200 words thanking supervisors, institution, AWS docs, open-source communities
  - Write Table of Contents listing all chapters and major subsections with section numbers
  - Write List of Figures enumerating every figure reference with descriptive captions
  - Write List of Abbreviations defining at least 20 technical acronyms (AWS, EC2, SNS, CPU, API, REST, SLA, MTTD, MTTR, ASG, IAM, SSM, SPA, UI, JSON, HTTP, CORS, SDK, CLI, APM)
  - Write Abstract of 600–800 words in past tense, third person, covering problem statement, solution, tech stack, key features, implementation, testing, results; include CPU thresholds (70%, 90%), polling intervals (20s backend, 30s frontend), AWS region (us-west-1), 10 REST API endpoints; end with Keywords line of at least 8 terms
  - _Requirements: 1.1, 1.4, 1.5, 1.6, 2.1, 2.2, 2.3, 2.4, 3.1, 3.2, 3.3, 3.4_

  - [ ]* 2.1 Write property test for front matter structure
    - **Property 1: All Twenty Sections Present in Order**
    - **Validates: Requirements 1.1**

  - [ ]* 2.2 Write property test for Abstract length and content
    - **Property 6: Abstract Length Within Range (600–800 words)**
    - **Property 7: Abstract Contains Required Technical Values (70%, 90%, 20 seconds, 30 seconds, us-west-1, 10 endpoints)**
    - **Property 8: Abstract Keywords Line (≥ 8 terms)**
    - **Validates: Requirements 3.1, 3.3, 3.4**

- [ ] 3. Append Chapter 1: Introduction (10–12 pages)
  - Use `fsAppend('docs/dissertation.md', ...)` to add Chapter 1
  - Write section 1.1 Background and Context: evolution from physical servers → virtualisation → cloud-native; AWS market context
  - Write section 1.2 Importance of Cloud Computing: uptime requirements, SLA implications, cost of downtime
  - Write section 1.3 Problem Statement: undetected EC2 crashes, CPU runaway processes, manual DevOps burden
  - Write section 1.4 Objectives of the Project: at least 5 numbered measurable goals referencing specific thresholds (e.g., "automate CPU-based healing within 20 seconds of threshold breach")
  - Write section 1.5 Scope of the Project: single region (us-west-1), EC2 only, no RDS/ECS
  - Write section 1.6 Motivation: real-world pain points
  - Write section 1.7 Real-World Applications: at least 3 industry scenarios (e-commerce, banking, SaaS)
  - Write section 1.8 Limitations of Current Approaches: manual console monitoring, alert fatigue, no auto-remediation
  - Include Manual vs Automated Recovery comparison table (detection time, response time, human effort, reliability, cost)
  - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.5, 4.6, 16.6_

  - [ ]* 3.1 Write property test for Chapter 1 subsections
    - **Property 9: Chapter 1 Required Subsections Present**
    - **Validates: Requirements 4.1**

- [ ] 4. Append Chapter 2: Literature Survey (10–12 pages)
  - Use `fsAppend('docs/dissertation.md', ...)` to add Chapter 2
  - Write one full paragraph each for 8 systems: AWS Auto Scaling, Kubernetes self-healing, Netflix Chaos Monkey, Prometheus + Grafana, Nagios, Zabbix, Datadog, PagerDuty
  - Include Literature Survey Summary Table with columns: Author/System, Year, Technology Used, Key Feature, Limitation — at least 8 rows
  - Write concluding subsection identifying the research gap: no surveyed system combines CPU-based healing + instance state recovery + live dashboard + SNS alerting in a single lightweight stack
  - All descriptions in academic prose paragraphs, not bullet lists
  - _Requirements: 5.1, 5.2, 5.3, 5.4, 5.5, 16.1, 16.6_

  - [ ]* 4.1 Write property test for literature survey references
    - **Property 11: Literature Survey References Eight Systems**
    - **Validates: Requirements 5.2**

- [ ] 5. Append Chapter 3: Existing System (6–8 pages)
  - Use `fsAppend('docs/dissertation.md', ...)` to add Chapter 3
  - Describe 3 existing system architectures: manual AWS Console monitoring, CloudWatch + SNS without auto-remediation, third-party APM tools (Datadog/New Relic)
  - Include Gap Analysis Table with columns: Feature, Existing System Capability, Proposed System Capability — at least 8 rows covering detection latency, auto-remediation, CPU-based healing, email alerting, dashboard visualisation, instance state tracking, recovery logging, cost
  - List at least 6 specific drawbacks in paragraph form: detection latency, no auto-remediation, alert fatigue, high cost, complex setup, no unified dashboard
  - _Requirements: 6.1, 6.2, 6.3, 6.4, 16.1, 16.6_

  - [ ]* 5.1 Write property test for Gap Analysis Table row count
    - **Property 12: Gap Analysis Table Row Count (≥ 8 rows)**
    - **Validates: Requirements 6.3**

- [ ] 6. Append Chapter 4: Proposed System (10–12 pages)
  - Use `fsAppend('docs/dissertation.md', ...)` to add Chapter 4
  - Write system overview and ASCII architecture diagram showing React Frontend → Flask Backend → AWS layers (EC2, CloudWatch, SNS, Auto Scaling, Lambda, SSM) with directional arrows; include figure caption and explanatory paragraph
  - Write one paragraph each for all 6 dashboard components: MetricCards, EC2StatusPanel, CPUUtilizationChart, CloudWatchAlarms, AutoScalingLogs, RecoveryEvents
  - Describe Backend Module: Flask REST API (10 endpoints), Monitor_Thread (20s polling), SNS integration, recovery_log (50-event cap)
  - Describe Cloud Infrastructure Module: EC2, CloudWatch, Auto Scaling, SNS, IAM, Lambda, SSM — role of each
  - Include text-based Data Flow Diagram showing complete auto-healing sequence from CPU spike → monitor detection → reboot → state transitions → recovery confirmation
  - List at least 5 advantages of proposed system over existing approaches in paragraph form
  - _Requirements: 7.1, 7.2, 7.3, 7.4, 7.5, 7.6, 7.7, 16.6_

  - [ ]* 6.1 Write property test for Chapter 4 dashboard component coverage
    - **Property 13: Chapter 4 Describes All Six Dashboard Components**
    - **Validates: Requirements 7.3**

- [ ] 7. Append Chapter 5: System Implementation (12–15 pages)
  - Use `fsAppend('docs/dissertation.md', ...)` to add Chapter 5
  - Include Tools and Technologies Table: Python 3, Flask 3.1.3, flask-cors 5.0.0, boto3, React 18, TypeScript, Vite, Tailwind CSS, Recharts, Framer Motion, shadcn-ui, Node.js, AWS CLI — with Version and Purpose columns
  - Describe AWS setup sequence referencing `demo_setup.py`: SNS topic creation, IAM role, EC2 instance creation (4 instances tagged `Project: auto-recovery`), CloudWatch alarms, ASG creation
  - Include 4 required code snippets from actual codebase: (a) `_monitor_loop` core logic, (b) `get_cpu` function, (c) `/api/heal` endpoint, (d) frontend useEffect + setInterval polling pattern at 30s
  - Include project folder structure as formatted tree: `Backend/`, `src/components/dashboard/`, `src/pages/`, `docs/`, root config files
  - Include Failure_Type classification table: CRITICAL_CPU, HIGH_CPU, INSTANCE_DOWN, STATUS_CHECK with trigger conditions and Action_Taken values
  - Describe Lambda auto-healing flow: CloudWatch Alarm → SNS Topic → Lambda Function → `ec2.reboot_instances()` → SNS email confirmation
  - _Requirements: 8.1, 8.2, 8.3, 8.4, 8.5, 8.6, 8.7, 16.6_

  - [ ]* 7.1 Write property test for Chapter 5 code snippet count
    - **Property 14: Chapter 5 Contains At Least Four Fenced Code Blocks**
    - **Validates: Requirements 8.4**

- [ ] 8. Checkpoint — verify file exists and chapters 1–5 are present
  - Ensure all tests pass, ask the user if questions arise.

- [ ] 9. Append Chapter 6: System Testing (6–8 pages)
  - Use `fsAppend('docs/dissertation.md', ...)` to add Chapter 6
  - Include Test Cases Table with columns: Test Case ID, Test Description, Input/Precondition, Expected Output, Actual Output, Status — at least 12 rows covering: all 10 API endpoint responses, CPU threshold detection at 70% and 90%, state transition logging, SNS email dispatch, manual heal trigger, dashboard data refresh, alarm state display, ASG activity display, recovery event ordering, CPU chart data rendering, error handling for missing instances, concurrent monitor thread safety
  - Describe stress testing methodology using `stress_demo.py` and `scenario_demo.py` with SSM to spike CPU without SSH keys
  - Describe instance termination test using `scenario_demo.py terminate` and expected recovery sequence in RecoveryEvents panel
  - Describe 2 negative test cases: (a) no instances tagged `Project: auto-recovery`, (b) SNS topic does not exist at startup
  - _Requirements: 9.1, 9.2, 9.3, 9.4, 9.5, 16.6_

  - [ ]* 9.1 Write property test for Test Cases Table row count
    - **Property 15: Test Cases Table Row Count (≥ 12 rows)**
    - **Validates: Requirements 9.2**

- [ ] 10. Append Chapter 7: Performance Analysis (6–8 pages)
  - Use `fsAppend('docs/dissertation.md', ...)` to add Chapter 7
  - Include Performance Metrics Table: backend poll interval (20s), frontend refresh interval (30s), max recovery log size (50 events), CPU metric period (300s / 5 min), CPU metric window (15 min current / 1h / 24h chart), API endpoint count (10)
  - Include MTTD/MTTR Comparison Table: proposed system vs manual monitoring across Mean Time to Detect, Mean Time to Recover, Human Effort Required, Notification Latency, Cost
  - Discuss scalability of tag-based instance discovery: linear scaling, one describe_instances result and one get_metric_statistics call per instance per 20s cycle
  - Discuss cost efficiency: Flask backend and React frontend run locally (zero cloud hosting cost); only AWS API calls (CloudWatch, EC2, SNS) incur cost — typically < $1/month for small fleet
  - _Requirements: 10.1, 10.2, 10.3, 10.4, 10.5, 16.6_

- [ ] 11. Append Chapter 8: Sample Code (8–10 pages)
  - Use `fsAppend('docs/dissertation.md', ...)` to add Chapter 8
  - Include complete `_monitor_loop` function with annotations: EC2 describe_instances call, state comparison logic, SNS publish calls, CPU threshold check, 20-second sleep
  - Include complete `_log_event` function with annotations for all 11 fields: type, status, message, time, instance_id, failure_reason, fix_applied, failure_type, action_taken, result, cpu_at_failure
  - Include `/api/recovery` endpoint with explanation of response shape: `{ events: [...], total_recoveries: number, last_recovery_time: string | null }`
  - Include `get_cpu` function with explanation of CloudWatch `get_metric_statistics` call, aligned time range calculation, datapoint sorting logic
  - Include frontend polling pattern: useEffect + setInterval at 30s from a dashboard component
  - Include `demo_setup.py` AWS resource creation sequence as numbered list with code excerpts showing EC2 instance creation, CloudWatch alarm creation, SNS topic setup
  - _Requirements: 11.1, 11.2, 11.3, 11.4, 11.5, 11.6, 11.7_

- [ ] 12. Append Chapter 9: Results and Discussion (6–8 pages)
  - Use `fsAppend('docs/dissertation.md', ...)` to add Chapter 9
  - Describe each of the 6 dashboard components' visual output in detail: what data is displayed and how it changes during a recovery event
  - Describe complete auto-healing sequence as observed in RecoveryEvents panel: "High CPU Alert — TRIGGERED" → state transitions → "Auto Recovery — COMPLETED"
  - Describe SNS email content format referencing actual message template in `app.py`: instance name, CPU%, failure type, action, timestamp, dashboard URL
  - Describe observed behaviour during `scenario_demo.py terminate`: running → stopping → stopped → pending → running
  - Include Results Summary Table: Objective, Expected Outcome, Observed Outcome, Status — mapping Chapter 1 objectives to observed results
  - _Requirements: 12.1, 12.2, 12.3, 12.4, 12.5, 12.6, 16.6_

- [ ] 13. Append Chapter 10: Conclusion and Future Enhancement (5–6 pages)
  - Use `fsAppend('docs/dissertation.md', ...)` to add Chapter 10
  - Summarise project contributions in paragraph form: background thread monitoring, dual-layer healing (Flask + Lambda), SNS alerting, React live dashboard
  - List at least 5 known limitations in paragraph form: in-memory recovery_log (lost on restart), single-region (us-west-1 only), no persistent database, no authentication on API endpoints, polling-based detection latency
  - Propose at least 6 future enhancements with a paragraph each: persistent database for recovery logs, multi-region support, predictive scaling using ML, Kubernetes migration, role-based access control, WebSocket-based real-time push
  - Write concluding paragraph of at least 150 words on academic and practical significance
  - _Requirements: 13.1, 13.2, 13.3, 13.4, 13.5, 16.6_

  - [ ]* 13.1 Write property test for Chapter 10 completeness
    - **Property 16: Chapter 10 Lists ≥ 5 Limitations and ≥ 6 Future Enhancements**
    - **Validates: Requirements 13.3, 13.4**

- [ ] 14. Append References section (2–3 pages)
  - Use `fsAppend('docs/dissertation.md', ...)` to add References
  - Write at least 20 IEEE-formatted citations: [N] Author(s), "Title," Source, Year
  - Cover: AWS official documentation (EC2, CloudWatch, SNS, Lambda, Auto Scaling, IAM, SSM), academic papers on cloud auto-scaling and self-healing, React, Flask, boto3, Recharts, Tailwind CSS, Framer Motion, NIST cloud computing definitions
  - Include URL and access date for all online references
  - _Requirements: 14.1, 14.2, 14.3, 14.4_

  - [ ]* 14.1 Write property test for References count
    - **Property 17: References Section Contains ≥ 20 IEEE Citations**
    - **Validates: Requirements 14.1**

- [ ] 15. Append Appendix section (3–4 pages)
  - Use `fsAppend('docs/dissertation.md', ...)` to add Appendix
  - Include API Reference Table with columns: Endpoint, Method, Description, Response Format — all 10 endpoints: `/api/instances`, `/api/summary`, `/api/alarms`, `/api/recovery`, `/api/cpu-metrics`, `/api/heal`, `/api/scaling`, `/api/sns/setup`, `/api/sns/status`, `/api/sns/subscribe`
  - Include AWS IAM policy permissions required by the system
  - Include complete project folder structure
  - Include `requirements.txt` contents (flask==3.1.3, flask-cors==5.0.0, boto3)
  - Include optional Publication abstract subsection
  - _Requirements: 15.1, 15.2, 15.3_

  - [ ]* 15.1 Write property test for API Reference Table completeness
    - **Property 18: API Reference Table Contains All 10 Endpoint Paths**
    - **Validates: Requirements 15.2**

- [ ] 16. Final checkpoint — verify complete document
  - Ensure all tests pass, ask the user if questions arise.

  - [ ]* 16.1 Write property test for technical constants accuracy
    - **Property 19: Technical Constants Accuracy (Flask 3.1.3, flask-cors 5.0.0, us-west-1, 20s, 30s, 70%, 90%, 50 events, CloudAutoRecoveryAlerts, Project: auto-recovery, 11 scripts, 10 endpoints)**
    - **Validates: Requirements 17.1–17.10**

  - [ ]* 16.2 Write property test for valid Markdown structure
    - **Property 20: Valid Markdown Structure (no unclosed code blocks, no malformed tables, no broken heading hierarchy)**
    - **Validates: Requirements 18.2**

  - [ ]* 16.3 Write property test for document length
    - **Property 2: Document Length Within Target Range (24,000–31,500 words)**
    - **Validates: Requirements 1.2**

  - [ ]* 16.4 Write property test for at least one table per chapter
    - **Property 10: At Least One Markdown Table Per Chapter (Chapters 1–10)**
    - **Validates: Requirements 16.6**

## Notes

- Tasks marked with `*` are optional and can be skipped for faster MVP
- Tasks must be executed in order — each `fsAppend` depends on the file created in task 2
- Each task references specific requirements for traceability
- Code snippets in tasks 7 and 11 must be extracted from the actual codebase, not paraphrased
- All technical constants (versions, thresholds, intervals, counts) must match the values in `design.md` exactly
