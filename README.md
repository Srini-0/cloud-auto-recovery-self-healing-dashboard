# ☁️ Cloud Auto-Recovery Self-Healing Dashboard

A full-stack cloud infrastructure monitoring and auto-recovery system built on AWS. It watches your EC2 instances 24/7, automatically detects failures and CPU spikes, heals them without manual intervention, and sends real-time email alerts — all visualized through a live React dashboard.

---

## 📸 Overview

When something goes wrong — an EC2 instance crashes, CPU spikes dangerously high, or a server stops responding — this system detects it within 20 seconds, takes corrective action automatically, and notifies you via email. No manual intervention required.

```
Instance CPU spikes → Detected in 20s → Auto-reboot triggered → Email sent → Dashboard updated
Instance crashes    → Detected in 20s → Auto-start triggered  → Email sent → Recovery logged
```

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────┐
│                React Frontend (Vite + TS)               │
│                   http://localhost:5173                 │
│                                                         │
│  MetricCards  EC2Panel  CPUChart  Alarms  RecoveryLog   │
└──────────────────────┬──────────────────────────────────┘
                       │ HTTP polling (every 30s)
                       ▼
┌─────────────────────────────────────────────────────────┐
│              Flask API Server (app.py)                  │
│                  http://localhost:5000                  │
│                                                         │
│  /api/instances   /api/summary    /api/alarms           │
│  /api/recovery    /api/cpu-metrics /api/heal            │
│  /api/scaling     /api/sns/setup  /api/sns/test         │
│                                                         │
│  Background Thread: polls EC2 every 20s                 │
│  → detects state changes                                │
│  → triggers reboot on high CPU                          │
│  → sends SNS email alerts                               │
└──────────────────────┬──────────────────────────────────┘
                       │ boto3 (AWS SDK)
                       ▼
┌─────────────────────────────────────────────────────────┐
│                    AWS (us-west-1)                      │
│                                                         │
│  EC2 Instances        CloudWatch Alarms                 │
│  Auto Scaling Group   SNS Topic + Email Subscriptions   │
│  IAM Roles            Lambda Function (optional)        │
└─────────────────────────────────────────────────────────┘
```

---

## ✨ Features

- **Real-Time Monitoring** — polls all tagged EC2 instances every 20 seconds for state changes
- **Auto CPU Healing** — automatically reboots instances when CPU exceeds 70% (critical at 90%+)
- **Auto Instance Recovery** — detects stopped/terminated instances and triggers restart
- **Email Alerts via SNS** — instant notifications for every failure and recovery event
- **Live Dashboard** — React UI with CPU charts, alarm states, scaling logs, and recovery timeline
- **Manual Heal Trigger** — one-click health check and heal from the dashboard
- **Lambda Integration** — optional serverless healing layer via CloudWatch → SNS → Lambda

---

## 🛠️ Tech Stack

### Frontend
| Technology | Purpose |
|---|---|
| React 18 + TypeScript | UI framework |
| Vite | Build tool and dev server |
| Tailwind CSS | Styling |
| shadcn/ui + Radix UI | Component library |
| Recharts | CPU utilization charts |
| Framer Motion | Animations |
| TanStack Query | Data fetching and caching |
| React Router | Client-side routing |

### Backend
| Technology | Purpose |
|---|---|
| Python + Flask | REST API server |
| boto3 | AWS SDK for Python |
| Threading | Background health monitor loop |
| Flask-CORS | Cross-origin request handling |

### AWS Services
| Service | Role |
|---|---|
| EC2 | Virtual servers being monitored and healed |
| CloudWatch | CPU and status check metric alarms |
| Auto Scaling | Automatically replaces terminated instances |
| SNS | Email alerts for every recovery event |
| IAM | Permissions for Lambda and SSM access |
| Lambda | Optional serverless auto-healing layer |
| SSM (Systems Manager) | Remote command execution for stress testing |

---

## 🚀 Getting Started

### Prerequisites

- Node.js 18+ and npm
- Python 3.9+
- AWS account with configured credentials (`aws configure`)
- EC2 instances tagged with `Project: auto-recovery` in `us-west-1`

### 1. Clone the Repository

```bash
git clone https://github.com/Srini-0/cloud-auto-recovery-self-healing-dashboard.git
cd cloud-auto-recovery-self-healing-dashboard
```

### 2. Set Up AWS Resources (First Time Only)

```bash
cd Backend
pip install -r requirements.txt
python demo_setup.py
```

This creates EC2 instances, CloudWatch alarms, an Auto Scaling Group, and an SNS topic. You'll be prompted for your email — confirm the subscription from your inbox before continuing.

Optionally deploy the Lambda auto-healing layer:

```bash
python setup_lambda.py
```

### 3. Start the Backend

```bash
cd Backend
python app.py
```

The Flask API server starts at `http://localhost:5000` and immediately begins monitoring your instances in the background.

### 4. Start the Frontend

```bash
npm install
npm run dev
```

Open `http://localhost:5173` to view the dashboard.

---

## 📊 Dashboard Components

| Component | Description |
|---|---|
| **Metric Cards** | Total instances, healthy count, unhealthy count, average CPU |
| **EC2 Status Panel** | Instance table with name, type, AZ, status, uptime, and CPU |
| **CPU Utilization Chart** | Live area chart per instance — 1h or 24h view |
| **CloudWatch Alarms** | Current alarm states with color-coded indicators |
| **Auto Scaling Logs** | Recent ASG launch and terminate activity |
| **Recovery Events** | Full log of every failure and recovery with failure type, action taken, and result |

---

## 🔄 Auto-Healing Flow

```
1.  Instance CPU spikes above 70%
          ↓
2.  Background monitor detects it (within 20 seconds)
          ↓
3.  Recovery event logged: "High CPU Alert — TRIGGERED"
          ↓
4.  ec2.reboot_instances() called automatically
          ↓
5.  SNS email sent: "🚨 High CPU Alert: prod-server-3 at 87%"
          ↓
6.  Instance state: running → stopping → stopped → pending → running
          ↓
7.  Each state change logged as a new recovery event
          ↓
8.  Final event logged: "Auto Recovery — COMPLETED"
          ↓
9.  SNS email sent: "✅ Recovery Complete: prod-server-3"
          ↓
10. Dashboard shows instance back as HEALTHY
```

---

## 🧰 Backend Scripts Reference

| Script | Purpose | When to Run |
|---|---|---|
| `app.py` | Flask API server — powers the dashboard | Always running during demo |
| `demo_setup.py` | One-time full AWS resource setup | First time only |
| `setup_lambda.py` | Deploy Lambda auto-healing function | After `demo_setup.py` |
| `start_demo.py` | Start stopped EC2 instances | Beginning of a session |
| `stop_demo.py` | Stop instances + clean up Lambda/IAM | End of a session |
| `stress_demo.py` | Spike CPU on instances to trigger alarms | During live demo |
| `scenario_demo.py` | Run specific scenarios (stress/terminate/recover) | During live demo |
| `status_demo.py` | Check current state of all instances | Anytime |
| `diagnose_sns.py` | Diagnose SNS email delivery issues | When emails aren't arriving |
| `fix_sns_email.py` | Re-subscribe an email to the SNS topic | When subscription was lost |
| `terminate_old.py` | Full teardown — delete all AWS resources | End of project / reset |

### Recommended Run Order

**First-time setup:**
```bash
python demo_setup.py → python setup_lambda.py → python app.py
```

**Daily demo session:**
```bash
python start_demo.py → python app.py → python stress_demo.py
```

**If emails aren't arriving:**
```bash
python fix_sns_email.py → python diagnose_sns.py
```

**Full reset:**
```bash
python terminate_old.py
```

---

## 🔌 API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/instances` | All project EC2 instances with CPU and status |
| `GET` | `/api/summary` | Total/healthy/unhealthy counts and average CPU |
| `GET` | `/api/alarms` | CloudWatch alarms for project instances |
| `GET` | `/api/scaling` | Auto Scaling Group activity log |
| `GET` | `/api/recovery` | Recovery event log (last 10 events) |
| `GET` | `/api/cpu-metrics` | CPU chart data (`?mode=1h` or `?mode=24h`) |
| `POST` | `/api/heal` | Manually trigger health check and heal |
| `POST` | `/api/sns/setup` | Create the SNS topic |
| `POST` | `/api/sns/test` | Send a test email to verify SNS |
| `GET` | `/api/sns/status` | SNS topic and subscription status |
| `POST` | `/api/sns/subscribe` | Subscribe an email to the SNS topic |

---

## 🏷️ Failure Type Classification

| Failure Type | Condition |
|---|---|
| `CRITICAL_CPU` | CPU ≥ 90% |
| `HIGH_CPU` | CPU > 70% and < 90% |
| `INSTANCE_DOWN` | Instance state → stopped / stopping / terminated |
| `STATUS_CHECK` | Instance state → pending (EC2 auto-recovery) |
| `HEALTHY` | No failure condition |

---

## 📁 Project Structure

```
├── Backend/
│   ├── app.py              # Flask API server + background health monitor
│   ├── demo_setup.py       # One-time AWS resource provisioning
│   ├── setup_lambda.py     # Lambda auto-healing deployment
│   ├── stress_demo.py      # CPU stress testing via SSM
│   ├── scenario_demo.py    # Demo scenario runner
│   ├── start_demo.py       # Start stopped instances
│   ├── stop_demo.py        # Stop instances + cleanup
│   ├── status_demo.py      # Quick status check
│   ├── diagnose_sns.py     # SNS email diagnostics
│   ├── fix_sns_email.py    # Re-subscribe email to SNS
│   ├── terminate_old.py    # Full AWS resource teardown
│   └── requirements.txt
├── src/
│   ├── components/
│   │   ├── dashboard/      # Dashboard UI components
│   │   └── ui/             # shadcn/ui base components
│   ├── pages/
│   │   └── Index.tsx       # Main dashboard page
│   └── App.tsx
├── docs/
│   ├── project-overview.md
│   ├── backend-scripts-guide.md
│   └── requirements/
├── package.json
└── vite.config.ts
```

---

## 🧪 Running Tests

```bash
npm run test
```

---
