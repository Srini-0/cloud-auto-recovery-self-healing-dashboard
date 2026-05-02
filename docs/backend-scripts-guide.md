# Backend Scripts Guide

This document explains what each Python script in the `Backend/` folder does, when to run it, and in what order.

---

## Overview — Script Roles

| Script | Purpose | When to Run |
|---|---|---|
| `demo_setup.py` | One-time full setup of all AWS resources | First time only |
| `setup_lambda.py` | Deploy Lambda auto-healing function | After demo_setup.py |
| `start_demo.py` | Start stopped EC2 instances | When instances are stopped |
| `stop_demo.py` | Stop running instances + cleanup Lambda/IAM | End of demo session |
| `stress_demo.py` | Spike CPU on instances to trigger alarms | During live demo |
| `scenario_demo.py` | Run specific demo scenarios (stress/terminate/recover) | During live demo |
| `status_demo.py` | Check current state of all instances | Anytime |
| `diagnose_sns.py` | Diagnose and fix SNS email alert issues | When emails aren't arriving |
| `fix_sns_email.py` | Re-subscribe a specific email to the SNS topic | When subscription was lost or deleted |
| `terminate_old.py` | Full teardown — delete everything | End of project / reset |
| `app.py` | Flask API server — powers the dashboard | Always running during demo |

---

## Script Details

### `app.py` — The Main API Server

This is the core backend. It runs as a Flask web server and provides all the data the dashboard UI reads.

**What it does:**
- Connects to AWS (EC2, CloudWatch, Auto Scaling, SNS) in `us-west-1`
- Runs a background health monitor thread every 20 seconds that watches instance state changes
- Automatically reboots instances if CPU goes above 70%
- Sends SNS email alerts for every recovery event
- Exposes these API endpoints for the frontend:

| Endpoint | What it returns |
|---|---|
| `GET /api/instances` | List of all project EC2 instances with CPU and status |
| `GET /api/summary` | Total/healthy/unhealthy count + average CPU |
| `GET /api/alarms` | CloudWatch alarms for project instances |
| `GET /api/scaling` | Auto Scaling Group activity log |
| `GET /api/recovery` | Recovery event log (last 50 events) |
| `GET /api/cpu-metrics` | CPU chart data (1h or 24h mode) |
| `POST /api/heal` | Manually trigger heal check on all instances |
| `POST /api/sns/setup` | Create the SNS topic |
| `POST /api/sns/test` | Send a test email to verify SNS is working |

**How to run:**
```bash
cd Backend
python app.py
```
Keep this running the entire time the dashboard is open.

---

### `demo_setup.py` — One-Time Full Setup

Run this once when setting up the project for the first time.

**What it does (in order):**
1. Creates an SNS topic and subscribes your email for alerts
2. Creates an IAM role with SSM permissions so instances can receive remote commands
3. Finds an existing EC2 instance to copy its AMI, subnet, and security group settings
4. Creates 4 demo EC2 instances tagged with `Project: auto-recovery`:
   - `prod-server-1` — healthy
   - `prod-server-2` — healthy
   - `prod-server-3` — intended for CPU stress demo
   - `prod-server-4` — intended for recovery demo
5. Creates CloudWatch alarms (CPU > 70% and status check failed) for each instance
6. Creates an Auto Scaling Group (min 1, desired 2, max 4)
7. Sends a setup complete email

**How to run:**
```bash
cd Backend
python demo_setup.py
```
You will be prompted to enter your email address. Check your inbox and confirm the SNS subscription before continuing.

---

### `setup_lambda.py` — Deploy Auto-Healing Lambda

Run this after `demo_setup.py` to add serverless auto-healing on top of the Flask monitor.

**What it does:**
1. Finds the existing SNS topic
2. Creates an IAM role for Lambda with EC2 + SNS + CloudWatch permissions
3. Writes and zips a Lambda function that reboots instances when alarms fire
4. Deploys the Lambda function to AWS
5. Connects SNS → Lambda (so alarms trigger the function automatically)
6. Updates all existing CloudWatch alarms to route through SNS → Lambda
7. Runs a test invocation to confirm it works

**How to run:**
```bash
cd Backend
python setup_lambda.py
```

After this, the auto-healing flow is:
```
CPU > 70% → CloudWatch Alarm → SNS → Lambda → Reboot Instance → Email sent
```

---

### `start_demo.py` — Start Stopped Instances

Use this to start all project instances that are currently stopped.

**What it does:**
- Finds all EC2 instances tagged `Project: auto-recovery` that are in `stopped` state
- Starts them all
- Waits 20 seconds then prints the current state of each

**How to run:**
```bash
cd Backend
python start_demo.py
```

---

### `stop_demo.py` — Stop Instances + Cleanup

Use this at the end of a demo session to stop instances and clean up Lambda/IAM.

**What it does:**
- Stops all running project instances
- Deletes the Lambda function (`CloudAutoRecoveryFunction`)
- Deletes the Lambda IAM role (`CloudAutoRecoveryLambdaRole`)

**How to run:**
```bash
cd Backend
python stop_demo.py
```

Note: This does NOT delete the instances or SNS topic — just stops them and removes Lambda.

---

### `stress_demo.py` — Spike CPU on Instances

Use this during a live demo to trigger the high CPU alarm and show auto-healing in action.

**What it does:**
- Lists all running project instances
- Lets you choose to stress all instances, one specific instance, or stop stress
- Uses AWS SSM (Systems Manager) to remotely run `stress-ng` on the instance — no SSH key needed
- Installs `stress-ng` automatically if not present

**How to run:**
```bash
cd Backend
python stress_demo.py
```

You'll get an interactive menu. Stressing an instance will spike its CPU to ~100% for a set duration (default 300 seconds), which triggers the CloudWatch alarm and the auto-healing flow.

**Requirement:** Instances must have the SSM IAM role attached (done by `demo_setup.py`).

---

### `scenario_demo.py` — Run Specific Demo Scenarios

A command-line tool for running specific demo scenarios quickly.

**What it does:**

| Command | Action |
|---|---|
| `python scenario_demo.py stress` | Stress `prod-server-3` via SSM to spike CPU |
| `python scenario_demo.py terminate` | Terminate `prod-server-4` to simulate a crash |
| `python scenario_demo.py recover` | Reboot or start `prod-server-4` to show recovery |
| `python scenario_demo.py status` | Print current state of all instances |

**How to run:**
```bash
cd Backend
python scenario_demo.py stress
python scenario_demo.py status
```

---

### `status_demo.py` — Quick Status Check

The simplest script — just prints the current state of all project instances.

**How to run:**
```bash
cd Backend
python status_demo.py
```

Output example:
```
🟢 prod-server-1 | i-0abc123 | running
🟢 prod-server-2 | i-0def456 | running
🔴 prod-server-3 | i-0ghi789 | stopped
```

---

### `fix_sns_email.py` — Re-Subscribe Email to SNS

A quick one-shot script to re-subscribe a specific email address to the SNS topic. Use this when the subscription was accidentally deleted, expired, or you need to re-add an email without running the full diagnostic.

**What it does:**
- Hardcodes the SNS topic ARN and email address directly in the script
- Calls `sns.subscribe()` to send a new confirmation email
- Prints instructions to confirm the subscription from your inbox

**How to run:**
```bash
cd Backend
python fix_sns_email.py
```

After running, check your inbox for an email from "AWS Notifications" and click the confirmation link. Then run `diagnose_sns.py` to verify it worked.

Note: The email and topic ARN are hardcoded in this file. Edit them at the top of the script if you need to use a different address.

---

### `diagnose_sns.py` — SNS Email Diagnostic

Use this when emails aren't arriving after setup. It walks through every possible failure point and tells you exactly what's wrong.

**What it does (in order):**
1. Verifies your AWS credentials are configured correctly
2. Checks if the `CloudAutoRecoveryAlerts` SNS topic exists — creates it if missing
3. Lists all subscriptions and shows whether each is confirmed or still pending
4. If no subscriptions exist, prompts you to enter an email and subscribes it on the spot
5. Sends a live test email to all confirmed subscribers to verify delivery end-to-end
6. Checks topic attributes to show confirmed vs pending subscription counts

**How to run:**
```bash
cd Backend
python diagnose_sns.py
```

Common issues it catches:
- Subscription is `PendingConfirmation` — you never clicked the confirmation link in your inbox
- No subscriptions at all — setup was skipped or the topic was recreated
- AWS credentials not configured — `aws configure` hasn't been run
- Topic doesn't exist — needs to be recreated

---

### `terminate_old.py` — Full Teardown / Reset

Use this to completely delete all AWS resources created by this project. Use with caution.

**What it deletes (in order):**
1. Auto Scaling Groups (scales to 0 first, then deletes)
2. Launch Templates
3. EC2 instances (terminates all tagged instances)
4. CloudWatch alarms
5. SNS topic
6. Lambda function
7. IAM roles

**How to run:**
```bash
cd Backend
python terminate_old.py
```

Run this when you want a clean slate or are done with the project entirely.

---

## Recommended Run Order

### First-time setup:
```
demo_setup.py → setup_lambda.py → app.py (keep running)
```

### Daily demo session:
```
start_demo.py → app.py (keep running) → stress_demo.py or scenario_demo.py
```

### If emails aren't arriving:
```
fix_sns_email.py → diagnose_sns.py
```

### End of session:
```
stop_demo.py
```

### Full reset:
```
terminate_old.py
```
