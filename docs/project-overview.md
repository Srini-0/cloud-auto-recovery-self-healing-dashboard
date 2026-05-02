# Cloud Auto-Recovery System — Project Overview

## What Is This Project?

This is a **Cloud Infrastructure Auto-Recovery Dashboard** — a full-stack web application that monitors AWS EC2 instances in real time, automatically detects failures, and heals them without any manual intervention.

Think of it as a self-driving operations center for your cloud servers. When something goes wrong — a server crashes, CPU spikes dangerously high, or an instance stops responding — the system detects it, fixes it, and sends you an email, all automatically.

---

## The Problem It Solves

In a real production environment, servers can fail at any time:
- An EC2 instance crashes or stops unexpectedly
- A runaway process spikes CPU to 100%, making the server unresponsive
- A deployment goes wrong and the instance becomes unhealthy

Without automation, an engineer has to:
1. Notice the problem (often from a user complaint)
2. Log into AWS console
3. Diagnose what happened
4. Manually restart or reboot the instance
5. Verify it recovered

This project eliminates all of that. The system watches your servers 24/7 and handles recovery automatically — usually within seconds.

---

## Who Is It For?

- **DevOps / Cloud engineers** who manage EC2 fleets and want automated self-healing
- **Startups and SaaS teams** who can't afford 24/7 on-call engineers watching servers
- **Demo / portfolio projects** showing real AWS infrastructure automation skills

---

## What It Does — Core Features

### 1. Real-Time Instance Monitoring
Every 20 seconds, the backend polls all EC2 instances tagged with `Project: auto-recovery` and checks their state. Any state change (running → stopped, stopped → pending, etc.) is detected and logged immediately.

### 2. Automatic CPU-Based Healing
If any running instance's CPU goes above **70%**, the system:
- Logs a `High CPU Alert` event
- Automatically reboots the instance to clear the spike
- Sends an email alert via SNS

If CPU reaches **90%+**, it's classified as `CRITICAL_CPU` and treated with higher urgency.

### 3. Automatic Instance Recovery
If an instance transitions to `stopped`, `stopping`, or `terminated`:
- A `Instance Down` event is logged
- An email alert is sent immediately
- When the instance enters `pending` (restarting), an `In-Progress` recovery event is logged
- When it returns to `running`, a `Recovery Complete` event is logged

### 4. Manual Heal Trigger
The dashboard has a "Trigger Heal" button that manually runs a health check across all instances and takes action on any that are unhealthy or have high CPU.

### 5. Email Alerts via SNS
Every significant event — instance down, recovery started, recovery complete, high CPU — sends an email to your subscribed address via AWS SNS. No polling required; you get notified the moment something happens.

### 6. Live Dashboard UI
A React frontend at `http://localhost:5173` shows:
- Summary cards: total instances, healthy count, unhealthy count, average CPU
- EC2 instance table: name, type, availability zone, status, uptime, CPU
- CPU utilization chart: live graph per instance (1h or 24h view)
- CloudWatch alarms: current state of all alarms
- Auto Scaling logs: recent ASG launch/terminate activity
- Recovery events: full log of every failure and recovery with details

---

## How It Works — Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    React Frontend (Vite)                 │
│              http://localhost:5173                       │
│                                                          │
│  MetricCards  EC2Panel  CPUChart  Alarms  RecoveryLog   │
└──────────────────────┬──────────────────────────────────┘
                       │ HTTP (every 30s)
                       ▼
┌─────────────────────────────────────────────────────────┐
│               Flask API Server (app.py)                  │
│              http://localhost:5000                       │
│                                                          │
│  /api/instances   /api/summary    /api/alarms           │
│  /api/recovery    /api/cpu-metrics /api/heal            │
│  /api/scaling     /api/sns/setup  /api/sns/test         │
│                                                          │
│  Background Thread: polls EC2 every 20s                 │
│  → detects state changes                                 │
│  → triggers reboot on high CPU                          │
│  → sends SNS emails                                     │
└──────────────────────┬──────────────────────────────────┘
                       │ boto3 (AWS SDK)
                       ▼
┌─────────────────────────────────────────────────────────┐
│                    AWS (us-west-1)                       │
│                                                          │
│  EC2 Instances        CloudWatch Alarms                 │
│  Auto Scaling Group   SNS Topic + Email Subscriptions   │
│  IAM Roles            Lambda Function (optional)        │
└─────────────────────────────────────────────────────────┘
```

---

## AWS Services Used

| Service | Role |
|---|---|
| EC2 | The virtual servers being monitored and healed |
| CloudWatch | Metric alarms for CPU and status checks |
| Auto Scaling | Automatically replaces terminated instances |
| SNS | Sends email alerts for every recovery event |
| IAM | Permissions for Lambda and SSM access |
| Lambda | Optional serverless auto-healing triggered by CloudWatch alarms |
| SSM (Systems Manager) | Remote command execution on instances (used by stress tools) |

---

## Implementation — How It Was Built

### Backend (Python / Flask)

The backend is a single Flask application (`app.py`) with two main parts:

**1. Background Health Monitor Thread**

When `app.py` starts, it immediately launches a background thread (`_monitor_loop`) that runs forever. Every 20 seconds it:
- Calls `ec2.describe_instances()` to get the current state of all project instances
- Compares each instance's current state to its previous state
- If a state change is detected, logs a recovery event and sends an SNS email
- If any running instance has CPU > 70%, triggers a reboot via `ec2.reboot_instances()`

This thread runs independently of any API requests — it's always watching, even when no one is looking at the dashboard.

**2. REST API Endpoints**

Flask exposes a set of JSON endpoints that the frontend polls every 30 seconds:
- Instance data comes from `ec2.describe_instances()` filtered by the `Project: auto-recovery` tag
- CPU data comes from `cloudwatch.get_metric_statistics()` for each instance
- Alarm data comes from `cloudwatch.describe_alarms()`
- Auto Scaling data comes from `autoscaling.describe_scaling_activities()`
- Recovery events come from an in-memory list (`recovery_log`) maintained by the monitor thread

**3. SNS Email Integration**

At startup, `app.py` looks up the `CloudAutoRecoveryAlerts` SNS topic ARN. Every time a significant event happens, it calls `sns.publish()` with a formatted email message. The frontend also has a "Test Email" button that calls `/api/sns/test` to verify the setup is working.

### Frontend (React / TypeScript / Vite)

The frontend is a single-page React app built with Vite and styled with Tailwind CSS. It uses Recharts for the CPU graph and Framer Motion for animations.

The main page (`Index.tsx`) fetches `/api/summary` and `/api/instances` every 30 seconds and passes the data down to child components:

- `MetricCards` — shows the 4 summary numbers at the top
- `EC2StatusPanel` — renders the instance table with status indicators and uptime
- `CPUUtilizationChart` — fetches `/api/cpu-metrics` and renders an area chart per instance, with 1h and 24h modes
- `CloudWatchAlarms` — fetches `/api/alarms` and shows alarm state with color-coded indicators
- `AutoScalingLogs` — fetches `/api/scaling` and shows recent ASG activity
- `RecoveryEvents` — fetches `/api/recovery` every 30 seconds and renders detailed event cards with failure reason, action taken, and result. Also contains the SNS email subscription panel.

### Demo Infrastructure Scripts

The `Backend/` folder contains Python scripts that manage the AWS resources used for the demo:

- `demo_setup.py` — creates all AWS resources from scratch (instances, alarms, ASG, SNS, IAM)
- `setup_lambda.py` — deploys a Lambda function that adds a second layer of auto-healing via CloudWatch → SNS → Lambda
- `stress_demo.py` / `scenario_demo.py` — trigger CPU stress or instance termination to demonstrate the recovery flow live
- `start_demo.py` / `stop_demo.py` — start and stop instances between sessions
- `diagnose_sns.py` — diagnoses SNS email issues (checks credentials, topic, subscriptions, sends a test email)
- `fix_sns_email.py` — re-subscribes a specific email to the SNS topic when the subscription was lost or deleted
- `terminate_old.py` — full teardown of all AWS resources

---

## The Auto-Healing Flow (End to End)

Here is exactly what happens when an instance fails:

```
1. Instance CPU spikes above 70%
        ↓
2. Background monitor detects it (within 20 seconds)
        ↓
3. Recovery event logged: "High CPU Alert — TRIGGERED"
        ↓
4. ec2.reboot_instances() called automatically
        ↓
5. SNS email sent: "🚨 High CPU Alert: prod-server-3 at 87%"
        ↓
6. Instance state: running → stopping → stopped → pending → running
        ↓
7. Each state change logged as a new recovery event
        ↓
8. Final event logged: "Auto Recovery — COMPLETED"
        ↓
9. SNS email sent: "✅ Recovery Complete: prod-server-3"
        ↓
10. Dashboard shows instance back as HEALTHY
```

The entire process — from detection to recovery — happens automatically with no human involvement.

---

## Running the Project

**Start the backend:**
```bash
cd Backend
pip install -r requirements.txt
python app.py
```

**Start the frontend:**
```bash
npm install
npm run dev
```

Open `http://localhost:5173` to see the dashboard.

The backend must be running at `http://localhost:5000` for the dashboard to work.
