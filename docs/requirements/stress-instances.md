# Stress Instances Requirements

## Introduction

`stress_demo.py` connects to all running EC2 instances tagged `Project=auto-recovery`
in `us-west-1` via SSH and runs CPU stress commands to trigger CloudWatch high-CPU
alarms during live demos.

## Key Requirements

### Instance Discovery
- Query EC2 for `Project=auto-recovery` tag, `running` state only
- Print name, instance ID, public IP before proceeding
- Exit gracefully if no running instances found

### SSH Connection
- Accept PEM key via `--key` arg or `EC2_KEY_PATH` env var; error and exit if missing
- Default SSH user: `ec2-user`; override with `--user`
- On connection failure: log, skip instance, continue to others

### CPU Stress
- Detect CPU core count on each instance
- Launch one stress worker per core (`stress --cpu N`)
- Fallback: `dd if=/dev/zero of=/dev/null` per core if `stress` not available
- Run as background processes (non-blocking SSH)

### Duration
- `--duration` arg (seconds), default 300s
- Terminate all stress processes after duration elapses

### Parallel Execution
- SSH + stress all instances simultaneously (not sequentially)
- Show summary of stressed vs failed instances
- Print status update every 30 seconds while waiting

### Graceful Interrupt
- Ctrl+C catches signal, terminates stress on all instances before exit
- Log cleanup progress; continue cleanup even if one instance fails
