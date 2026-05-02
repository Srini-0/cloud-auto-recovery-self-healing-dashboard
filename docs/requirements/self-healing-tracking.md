# Self-Healing Tracking Requirements

## Introduction

Enriches the EC2 auto-recovery dashboard with full context for every healing event.
Wires up the backend to fully populate all event fields, classifies failures into typed
categories, captures CPU at the moment of failure, records the concrete action taken
and its outcome, and reshapes the `/api/recovery` response to match the shape the
frontend already expects.

## Key Requirements

### Failure_Type Classification
- CPU > 90% → `CRITICAL_CPU`
- CPU > 70% and ≤ 90% → `HIGH_CPU`
- Instance state → stopped/stopping/terminated/shutting-down → `INSTANCE_DOWN`
- Instance state → pending (EC2 auto-recovery) → `STATUS_CHECK`
- No failure condition → `HEALTHY`

### Action_Taken Values
- `ec2.reboot_instances()` called → `REBOOT_INSTANCE`
- `ec2.start_instances()` called → `START_INSTANCE`
- State transition logged, no AWS action → `MONITORING`
- Healthy instance → `NONE`

### CPU_At_Failure
- CPU threshold breach events → float rounded to 1 decimal place
- Non-CPU events (INSTANCE_DOWN, STATUS_CHECK, HEALTHY) → `null`

### Result Field
- `REBOOT_INSTANCE` → `"Reboot command issued — instance will restart within 60s"`
- `START_INSTANCE` → `"Start command issued — instance transitioning to running"`
- Status `COMPLETED` → `"Instance recovered and passed health check"`
- `MONITORING` → `"Monitoring — awaiting recovery trigger"`
- `NONE` → `null`

### `/api/recovery` Response Shape
Returns `{ events, total_recoveries, last_recovery_time }`:
- `events` → 10 most recent healing events
- `total_recoveries` → count of events with status `COMPLETED` or `TRIGGERED`
- `last_recovery_time` → time of most recent such event, or `null`
- Empty log → placeholder healthy event, `total_recoveries: 0`, `last_recovery_time: null`

### `_log_event()` Signature
Accept optional kwargs: `failure_type`, `action_taken`, `cpu_at_failure`, `result` (all default `null`).
All 8+ fields stored in every event dict.
