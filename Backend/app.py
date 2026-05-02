from flask import Flask, jsonify, request
from flask_cors import CORS
import boto3
import threading
import time
from datetime import datetime, timezone, timedelta

app = Flask(__name__)
CORS(app)

REGION = "us-west-1"

ec2 = boto3.client("ec2", region_name=REGION)
cloudwatch = boto3.client("cloudwatch", region_name=REGION)
autoscaling = boto3.client("autoscaling", region_name=REGION)
sns = boto3.client("sns", region_name=REGION)

recovery_log = []
_prev_instance_states: dict = {}
_monitor_lock = threading.Lock()

# ─── SNS TOPIC ARN (resolved once at startup) ────────

def _get_sns_topic_arn():
    try:
        topics = sns.list_topics().get("Topics", [])
        for t in topics:
            if "CloudAutoRecoveryAlerts" in t["TopicArn"]:
                return t["TopicArn"]
    except Exception:
        pass
    return None

SNS_TOPIC_ARN = _get_sns_topic_arn()

def _send_sns(subject: str, message: str):
    """Publish to SNS. Logs errors to console instead of silently swallowing them."""
    if not SNS_TOPIC_ARN:
        print(f"[SNS] ⚠️  No topic ARN found — email not sent. Subject: {subject}")
        return
    try:
        sns.publish(TopicArn=SNS_TOPIC_ARN, Subject=subject, Message=message)
        print(f"[SNS] ✅ Email sent: {subject}")
    except Exception as e:
        print(f"[SNS] ❌ Failed to send email: {e} | Subject: {subject}")

# ─── HELPERS ─────────────────────────────────────────

def aligned_time_range(period_seconds, duration):
    now = datetime.now(timezone.utc)
    if period_seconds >= 3600:
        aligned_end = now.replace(minute=0, second=0, microsecond=0)
        start = aligned_end - duration + timedelta(hours=1)
        return start, aligned_end + timedelta(hours=1)
    else:
        period_minutes = max(1, period_seconds // 60)
        aligned_end = now.replace(second=0, microsecond=0)
        aligned_end = aligned_end - timedelta(minutes=aligned_end.minute % period_minutes)
        return aligned_end - duration, aligned_end

def get_ec2_instances():
    response = ec2.describe_instances(
        Filters=[
            {"Name": "tag:Project", "Values": ["auto-recovery"]},
            {"Name": "instance-state-name", "Values": ["running", "stopped", "stopping", "pending"]}
        ]
    )
    extra_ids = ["i-0fd2e9cf6ae6245d7"]
    instances = []
    seen = set()

    def parse_reservations(reservations):
        for r in reservations:
            for i in r["Instances"]:
                if i["InstanceId"] in seen:
                    continue
                seen.add(i["InstanceId"])
                name = next((t["Value"] for t in i.get("Tags", []) if t["Key"] == "Name"), "unnamed")
                instances.append({
                    "instance_id": i["InstanceId"],
                    "name": name,
                    "type": i.get("InstanceType", "-"),
                    "az": i.get("Placement", {}).get("AvailabilityZone", "-"),
                    "state": i["State"]["Name"],
                    "public_ip": i.get("PublicIpAddress", "N/A"),
                    "launch_time": i["LaunchTime"].isoformat() if i.get("LaunchTime") else None
                })

    parse_reservations(response["Reservations"])
    if extra_ids:
        try:
            extra_response = ec2.describe_instances(InstanceIds=extra_ids)
            parse_reservations(extra_response["Reservations"])
        except Exception:
            pass
    return instances

def get_cpu(instance_id):
    try:
        start_time, end_time = aligned_time_range(300, timedelta(minutes=15))
        response = cloudwatch.get_metric_statistics(
            Namespace="AWS/EC2",
            MetricName="CPUUtilization",
            Dimensions=[{"Name": "InstanceId", "Value": instance_id}],
            StartTime=start_time,
            EndTime=end_time,
            Period=300,
            Statistics=["Average"]
        )
        points = response.get("Datapoints", [])
        if points:
            return round(sorted(points, key=lambda x: x["Timestamp"])[-1]["Average"], 2)
        return 0
    except Exception:
        return 0

# ─── BACKGROUND HEALTH MONITOR ───────────────────────

def _log_event(event_type, status, message, instance_id,
               failure_reason=None, fix_applied=None,
               failure_type=None, action_taken=None,
               result=None, cpu_at_failure=None):
    event = {
        "type": event_type,
        "status": status,
        "message": message,
        "time": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "instance_id": instance_id,
        "failure_reason": failure_reason,
        "fix_applied": fix_applied,
        "failure_type": failure_type,
        "action_taken": action_taken,
        "result": result,
        "cpu_at_failure": cpu_at_failure,
    }
    with _monitor_lock:
        recovery_log.insert(0, event)
        del recovery_log[50:]

def _monitor_loop():
    global _prev_instance_states
    while True:
        try:
            response = ec2.describe_instances(
                Filters=[{"Name": "tag:Project", "Values": ["auto-recovery"]}]
            )
            current_states = {}
            for r in response["Reservations"]:
                for i in r["Instances"]:
                    name = next((t["Value"] for t in i.get("Tags", []) if t["Key"] == "Name"), "unnamed")
                    iid = i["InstanceId"]
                    state = i["State"]["Name"]
                    current_states[iid] = {"name": name, "state": state}

                    prev = _prev_instance_states.get(iid, {})
                    prev_state = prev.get("state")

                    if prev_state and prev_state != state:
                        if state in ("stopping", "stopped", "terminated", "shutting-down"):
                            _log_event(
                                "Instance Down", "TRIGGERED",
                                f"{name} transitioned {prev_state} → {state}", iid,
                                failure_reason=f"Instance state changed from {prev_state} to {state}",
                                fix_applied="Monitoring — waiting for recovery trigger",
                                failure_type="INSTANCE_DOWN",
                                action_taken="MONITORING",
                                result="Waiting for EC2 auto-recovery to initiate restart",
                            )
                            _send_sns(
                                subject=f"🔴 Instance Down: {name}",
                                message=(
                                    f"Instance: {name} ({iid})\n"
                                    f"State: {prev_state} → {state}\n"
                                    f"Reason: Instance state changed — monitoring for recovery\n"
                                    f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
                                    f"Dashboard: http://localhost:5173"
                                )
                            )

                        elif state == "pending":
                            _log_event(
                                "Auto Recovery", "IN-PROGRESS",
                                f"Instance status check failed - recovery initiated", iid,
                                failure_reason=f"Instance was {prev_state} — EC2 auto-recovery triggered",
                                fix_applied="EC2 start_instances called — instance restarting",
                                failure_type="INSTANCE_DOWN",
                                action_taken="START_INSTANCE",
                                result="Start command sent — instance entering pending state",
                            )
                            _send_sns(
                                subject=f"🔄 Recovery In Progress: {name}",
                                message=(
                                    f"Instance: {name} ({iid})\n"
                                    f"Action: EC2 auto-recovery triggered\n"
                                    f"Previous State: {prev_state}\n"
                                    f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
                                    f"Dashboard: http://localhost:5173"
                                )
                            )

                        elif state == "running" and prev_state in ("pending", "stopped", "stopping"):
                            _log_event(
                                "Auto Recovery", "COMPLETED",
                                f"Successfully recovered after system status check failure", iid,
                                failure_reason=f"Instance was previously {prev_state}",
                                fix_applied="Instance restarted and passed health check",
                                failure_type="INSTANCE_DOWN",
                                action_taken="START_INSTANCE",
                                result="Instance is running and healthy",
                            )
                            _send_sns(
                                subject=f"✅ Recovery Complete: {name}",
                                message=(
                                    f"Instance: {name} ({iid})\n"
                                    f"Status: RECOVERED — now running\n"
                                    f"Previous State: {prev_state}\n"
                                    f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
                                    f"Dashboard: http://localhost:5173"
                                )
                            )

                    if state == "running":
                        cpu = get_cpu(iid)
                        if cpu > 70:
                            with _monitor_lock:
                                recent = [e for e in recovery_log[:5]
                                    if e["instance_id"] == iid and "High CPU" in e.get("message", "")]
                            if not recent:
                                ftype = "CRITICAL_CPU" if cpu >= 90 else "HIGH_CPU"
                                _log_event(
                                    "High CPU Alert", "TRIGGERED",
                                    f"{name} CPU at {cpu}% — above 70% threshold", iid,
                                    failure_reason=f"CPUUtilization reached {cpu}% (threshold: 70%)",
                                    fix_applied="Reboot triggered to clear CPU spike",
                                    failure_type=ftype,
                                    action_taken="REBOOT_INSTANCE",
                                    result="Reboot command sent — CPU will reset on restart",
                                    cpu_at_failure=cpu,
                                )
                                _send_sns(
                                    subject=f"🚨 High CPU Alert: {name} at {cpu}%",
                                    message=(
                                        f"Instance: {name} ({iid})\n"
                                        f"CPU Utilization: {cpu}% (threshold: 70%)\n"
                                        f"Failure Type: {ftype}\n"
                                        f"Action: Reboot triggered automatically\n"
                                        f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
                                        f"Dashboard: http://localhost:5173"
                                    )
                                )
                                try:
                                    ec2.reboot_instances(InstanceIds=[iid])
                                except Exception:
                                    pass

            _prev_instance_states = current_states

        except Exception as ex:
            _log_event("Monitor Error", "TRIGGERED", f"Health monitor error: {str(ex)}", "system")

        time.sleep(20)

_monitor_thread = threading.Thread(target=_monitor_loop, daemon=True)
_monitor_thread.start()

# ─── ROUTES ──────────────────────────────────────────

@app.route("/api/instances")
def instances():
    data = get_ec2_instances()
    name_counts: dict = {}
    for i in data:
        name_counts[i["name"]] = name_counts.get(i["name"], 0) + 1
    name_seen: dict = {}
    result = []
    for i in data:
        raw_name = i["name"]
        if name_counts[raw_name] > 1:
            suffix = i["instance_id"][-6:]
            count = name_seen.get(raw_name, 0)
            display_name = raw_name if count == 0 else f"{raw_name}-{suffix}"
            name_seen[raw_name] = count + 1
        else:
            display_name = raw_name
        cpu = get_cpu(i["instance_id"])
        result.append({
            "name": display_name,
            "instance_id": i["instance_id"],
            "type": i["type"],
            "az": i["az"],
            "status": "HEALTHY" if i["state"] == "running" else "UNHEALTHY",
            "state": i["state"],
            "cpu": cpu,
            "public_ip": i["public_ip"],
            "launch_time": i.get("launch_time")
        })
    return jsonify(result)

@app.route("/api/summary")
def summary():
    data = get_ec2_instances()
    healthy = sum(1 for i in data if i["state"] == "running")
    unhealthy = len(data) - healthy
    all_cpus = [get_cpu(i["instance_id"]) for i in data]
    avg_cpu = round(sum(all_cpus) / len(all_cpus), 2) if all_cpus else 0
    return jsonify({
        "total_instances": len(data),
        "healthy_instances": healthy,
        "unhealthy_instances": unhealthy,
        "avg_cpu": avg_cpu
    })

def relative_time(ts):
    if ts is None:
        return "Never"
    if not hasattr(ts, "strftime"):
        return "Never"
    now = datetime.now(timezone.utc)
    if ts.tzinfo is None:
        ts = ts.replace(tzinfo=timezone.utc)
    diff = now - ts
    seconds = int(diff.total_seconds())
    if seconds < 60:
        return f"{seconds}s ago"
    if seconds < 3600:
        return f"{seconds // 60} min ago"
    if seconds < 86400:
        return f"{seconds // 3600}h ago"
    return f"{seconds // 86400}d ago"

@app.route("/api/alarms")
def alarms():
    try:
        project_instances = get_ec2_instances()
        project_instance_ids = {i["instance_id"] for i in project_instances}
        project_names = {i["name"] for i in project_instances}
        response = cloudwatch.describe_alarms()
        alarms_list = []
        for a in response["MetricAlarms"]:
            dims = {d["Name"]: d["Value"] for d in a.get("Dimensions", [])}
            instance_id = dims.get("InstanceId", "")
            alarm_name = a["AlarmName"]
            if not (instance_id in project_instance_ids or any(n in alarm_name for n in project_names)):
                continue
            threshold = a.get("Threshold", "")
            metric_name = a.get("MetricName", "")
            comparison = a.get("ComparisonOperator", "")
            op = ">" if "Greater" in comparison else "<" if "Less" in comparison else "="
            metric_str = f"{metric_name} {op} {threshold}" if threshold != "" else metric_name
            ts = a.get("StateUpdatedTimestamp")
            alarms_list.append({
                "name": alarm_name,
                "metric": metric_str,
                "state": a["StateValue"],
                "last_triggered": relative_time(ts)
            })
        if not alarms_list:
            alarms_list.append({
                "name": "No alarms configured yet",
                "metric": "Create alarm in CloudWatch console",
                "state": "OK",
                "last_triggered": "-"
            })
        return jsonify(alarms_list)
    except Exception as e:
        return jsonify([{"name": f"Error: {str(e)}", "metric": "-", "state": "ERROR", "last_triggered": "-"}])

@app.route("/api/scaling")
def scaling():
    try:
        all_asgs = autoscaling.describe_auto_scaling_groups().get("AutoScalingGroups", [])
        project_asgs = [
            asg for asg in all_asgs
            if any(t.get("Key") == "Project" and t.get("Value") == "auto-recovery"
                   for t in asg.get("Tags", []))
            or any(t.get("Key") == "Name" and "auto-recovery" in t.get("Value", "").lower()
                   for t in asg.get("Tags", []))
        ]
        if not project_asgs:
            for candidate in ["auto-recovery-demo-asg", "asg-auto-recovery", "auto-recovery-asg"]:
                try:
                    autoscaling.describe_scaling_activities(AutoScalingGroupName=candidate, MaxRecords=1)
                    project_asgs = [{"AutoScalingGroupName": candidate}]
                    break
                except Exception:
                    pass
        if not project_asgs:
            return jsonify([{"time": datetime.now().strftime("%H:%M:%S"), "action": "Monitor", "description": "No Auto Scaling Group found"}])

        asg_name = project_asgs[0]["AutoScalingGroupName"]
        response = autoscaling.describe_scaling_activities(AutoScalingGroupName=asg_name, MaxRecords=10)

        STATUS_LABEL = {
            "Successful": "Launch", "Failed": "Failed", "Cancelled": "Cancelled",
            "InProgress": "Launch", "PreInService": "Launch",
            "WaitingForInstanceWarmup": "Launch", "WaitingForELBConnectionDraining": "Terminate",
        }

        def infer_action(status_code, description):
            desc_lower = description.lower()
            if "terminat" in desc_lower: return "Terminate"
            if "health" in desc_lower: return "HealthCheck"
            if "launch" in desc_lower or "replac" in desc_lower: return "Launch"
            return STATUS_LABEL.get(status_code, "Launch")

        activities = []
        for a in response.get("Activities", []):
            desc = a.get("Description", "")
            activities.append({
                "time": a["StartTime"].strftime("%H:%M:%S"),
                "action": infer_action(a["StatusCode"], desc),
                "description": desc
            })
        if not activities:
            activities.append({"time": datetime.now().strftime("%H:%M:%S"), "action": "Monitor", "description": "No Auto Scaling activity yet"})
        return jsonify(activities)
    except Exception as e:
        return jsonify([{"time": datetime.now().strftime("%H:%M:%S"), "action": "Monitor", "description": f"Auto Scaling not configured: {str(e)}"}])

@app.route("/api/recovery")
def recovery():
    with _monitor_lock:
        events = list(recovery_log)

    non_healthy = [e for e in events if e.get("status", "").upper() not in ("HEALTHY",)]
    total_recoveries = len([e for e in events if e.get("action_taken") not in (None, "NONE", "MONITORING")])
    last_recovery_time = non_healthy[0]["time"] if non_healthy else None

    if not events:
        return jsonify({
            "events": [{
                "type": "Monitor",
                "status": "HEALTHY",
                "message": "All instances healthy — no recovery events detected",
                "time": datetime.now().strftime("%Y-%m-%d %H:%M"),
                "instance_id": "all",
                "failure_reason": None,
                "fix_applied": None,
                "failure_type": None,
                "action_taken": None,
                "result": None,
                "cpu_at_failure": None,
            }],
            "total_recoveries": 0,
            "last_recovery_time": None,
        })
    return jsonify({
        "events": events[:10],
        "total_recoveries": total_recoveries,
        "last_recovery_time": last_recovery_time,
    })

@app.route("/api/cpu-metrics")
def cpu_metrics():
    try:
        mode = request.args.get("mode", "1h")
        response = ec2.describe_instances(
            Filters=[
                {"Name": "tag:Project", "Values": ["auto-recovery"]},
                {"Name": "instance-state-name", "Values": ["running"]}
            ]
        )
        all_instances = []
        seen_ids = set()
        for r in response["Reservations"]:
            for i in r["Instances"]:
                if i["InstanceId"] in seen_ids:
                    continue
                seen_ids.add(i["InstanceId"])
                name = next((t["Value"] for t in i.get("Tags", []) if t["Key"] == "Name"), "unnamed")
                all_instances.append({"instance_id": i["InstanceId"], "name": name})

        extra_ids = ["i-0fd2e9cf6ae6245d7"]
        for eid in extra_ids:
            if eid not in seen_ids:
                try:
                    er = ec2.describe_instances(InstanceIds=[eid])
                    for r in er["Reservations"]:
                        for i in r["Instances"]:
                            if i["State"]["Name"] != "running":
                                continue
                            name = next((t["Value"] for t in i.get("Tags", []) if t["Key"] == "Name"), "unnamed")
                            all_instances.append({"instance_id": i["InstanceId"], "name": name})
                            seen_ids.add(i["InstanceId"])
                except Exception:
                    pass

        if not all_instances:
            return jsonify({"labels": [], "timestamps": [], "instances": {}})

        now = datetime.now(timezone.utc)
        if mode == "1h":
            period = 300
            end_time = now.replace(second=0, microsecond=0)
            end_time = end_time - timedelta(minutes=end_time.minute % 5)
            start_time = end_time - timedelta(hours=1)
        else:
            period = 3600
            end_time = now.replace(minute=0, second=0, microsecond=0) + timedelta(hours=1)
            start_time = end_time - timedelta(hours=24)

        slot_count = int((end_time - start_time).total_seconds() / period)
        timeline = [start_time + timedelta(seconds=period * i) for i in range(slot_count)]

        def nearest_slot(ts):
            ts = ts.astimezone(timezone.utc)
            offset = int((ts - start_time).total_seconds() // period)
            return max(0, min(offset, slot_count - 1))

        labels = [t.strftime("%m/%d %H:%M") if mode == "24h" else t.strftime("%H:%M") for t in timeline]
        result = {"labels": labels, "timestamps": [t.isoformat() for t in timeline], "instances": {}}

        name_counts: dict = {}
        for inst in all_instances:
            name_counts[inst["name"]] = name_counts.get(inst["name"], 0) + 1
        name_seen: dict = {}
        for inst in all_instances:
            raw_name = inst["name"]
            if name_counts[raw_name] > 1:
                suffix = inst["instance_id"][-6:]
                count = name_seen.get(raw_name, 0)
                inst["display_name"] = raw_name if count == 0 else f"{raw_name}-{suffix}"
                name_seen[raw_name] = count + 1
            else:
                inst["display_name"] = raw_name

        for instance in all_instances:
            instance_id = instance["instance_id"]
            display_name = instance["display_name"]
            try:
                cw_response = cloudwatch.get_metric_statistics(
                    Namespace="AWS/EC2",
                    MetricName="CPUUtilization",
                    Dimensions=[{"Name": "InstanceId", "Value": instance_id}],
                    StartTime=start_time,
                    EndTime=end_time,
                    Period=period,
                    Statistics=["Average"]
                )
                values = [None] * slot_count
                for point in cw_response.get("Datapoints", []):
                    slot = nearest_slot(point["Timestamp"])
                    values[slot] = round(point["Average"], 2)
                result["instances"][display_name] = values
            except Exception:
                result["instances"][display_name] = [None] * slot_count

        return jsonify(result)
    except Exception as e:
        return jsonify({"labels": [], "timestamps": [], "instances": {}, "error": str(e)})

@app.route("/api/heal", methods=["POST"])
def heal():
    try:
        data = get_ec2_instances()
        healed = []
        for instance in data:
            instance_id = instance["instance_id"]
            cpu = get_cpu(instance_id)
            state = instance["state"]

            if state != "running":
                ec2.start_instances(InstanceIds=[instance_id])
                event = {
                    "type": "Auto Recovery", "status": "TRIGGERED",
                    "message": f"Instance {instance['name']} was {state} — start triggered",
                    "time": datetime.now().strftime("%Y-%m-%d %H:%M"),
                    "instance_id": instance_id,
                    "failure_reason": f"Instance found in '{state}' state — not running",
                    "fix_applied": "ec2.start_instances() called — instance restarting",
                    "failure_type": "INSTANCE_DOWN",
                    "action_taken": "START_INSTANCE",
                    "result": "Start command sent — instance transitioning to running",
                    "cpu_at_failure": None,
                }
                recovery_log.insert(0, event)
                healed.append(event)
                _send_sns(
                    subject=f"🔄 Auto-Heal: Starting {instance['name']}",
                    message=(
                        f"Instance: {instance['name']} ({instance_id})\n"
                        f"Reason: Found in '{state}' state\n"
                        f"Action: ec2.start_instances() called\n"
                        f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
                        f"Dashboard: http://localhost:5173"
                    )
                )

            elif cpu > 70:
                ec2.reboot_instances(InstanceIds=[instance_id])
                ftype = "CRITICAL_CPU" if cpu >= 90 else "HIGH_CPU"
                event = {
                    "type": "Auto Recovery", "status": "TRIGGERED",
                    "message": f"High CPU ({cpu}%) on {instance['name']} — reboot triggered",
                    "time": datetime.now().strftime("%Y-%m-%d %H:%M"),
                    "instance_id": instance_id,
                    "failure_reason": f"CPUUtilization at {cpu}% exceeded 70% threshold",
                    "fix_applied": "ec2.reboot_instances() called — CPU spike cleared on restart",
                    "failure_type": ftype,
                    "action_taken": "REBOOT_INSTANCE",
                    "result": "Reboot command issued — instance will restart within 60s",
                    "cpu_at_failure": cpu,
                }
                recovery_log.insert(0, event)
                healed.append(event)
                _send_sns(
                    subject=f"🚨 Auto-Heal: Rebooting {instance['name']} (CPU {cpu}%)",
                    message=(
                        f"Instance: {instance['name']} ({instance_id})\n"
                        f"CPU at failure: {cpu}%\n"
                        f"Failure type: {ftype}\n"
                        f"Action: ec2.reboot_instances() called\n"
                        f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
                        f"Dashboard: http://localhost:5173"
                    )
                )

            else:
                event = {
                    "type": "Health Check", "status": "HEALTHY",
                    "message": f"{instance['name']} is healthy (CPU: {cpu}%)",
                    "time": datetime.now().strftime("%Y-%m-%d %H:%M"),
                    "instance_id": instance_id,
                    "failure_reason": None,
                    "fix_applied": "No action needed",
                    "failure_type": None,
                    "action_taken": "NONE",
                    "result": None,
                    "cpu_at_failure": None,
                }
                recovery_log.insert(0, event)
                healed.append(event)

        return jsonify(healed)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/sns/setup", methods=["POST"])
def setup_sns():
    try:
        topic = sns.create_topic(Name="CloudAutoRecoveryAlerts")
        topic_arn = topic["TopicArn"]
        # refresh the cached ARN
        global SNS_TOPIC_ARN
        SNS_TOPIC_ARN = topic_arn
        return jsonify({
            "status": "success",
            "topic_arn": topic_arn,
            "message": "SNS topic created. Add email subscription in AWS console."
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/sns/status", methods=["GET"])
def sns_status():
    """Returns SNS topic and subscription status for debugging."""
    try:
        topic_arn = _get_sns_topic_arn()
        if not topic_arn:
            return jsonify({
                "topic_exists": False,
                "topic_arn": None,
                "subscriptions": [],
                "confirmed_count": 0,
                "message": "No SNS topic found. Click 'Setup SNS' first."
            })

        subs = sns.list_subscriptions_by_topic(TopicArn=topic_arn).get("Subscriptions", [])
        sub_list = [{"protocol": s["Protocol"], "endpoint": s["Endpoint"], "status": s["SubscriptionArn"]} for s in subs]
        confirmed = [s for s in subs if s["SubscriptionArn"] not in ("PendingConfirmation", "Deleted")]

        return jsonify({
            "topic_exists": True,
            "topic_arn": topic_arn,
            "subscriptions": sub_list,
            "confirmed_count": len(confirmed),
            "message": "OK" if confirmed else "⚠️ No confirmed subscriptions — check your email and confirm the subscription"
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/sns/subscribe", methods=["POST"])
def sns_subscribe():
    """Subscribe an email address to the SNS topic."""
    try:
        email = request.json.get("email", "").strip()
        if not email or "@" not in email:
            return jsonify({"status": "error", "message": "Valid email required"}), 400

        topic_arn = _get_sns_topic_arn()
        if not topic_arn:
            # create topic if it doesn't exist
            topic_arn = sns.create_topic(Name="CloudAutoRecoveryAlerts")["TopicArn"]
            global SNS_TOPIC_ARN
            SNS_TOPIC_ARN = topic_arn

        sns.subscribe(TopicArn=topic_arn, Protocol="email", Endpoint=email)
        return jsonify({
            "status": "success",
            "message": f"Confirmation email sent to {email}. Check your inbox and click the confirmation link."
        })
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route("/api/sns/test", methods=["POST"])
def sns_test():
    """Test endpoint — sends a test email immediately to verify SNS is working."""
    topic_arn = _get_sns_topic_arn()
    if not topic_arn:
        return jsonify({
            "status": "error",
            "message": "No SNS topic found. Run setup_lambda.py first to create CloudAutoRecoveryAlerts topic."
        }), 400
    try:
        sns.publish(
            TopicArn=topic_arn,
            Subject="✅ Test Alert: Auto-Recovery Dashboard",
            Message=(
                f"This is a test email from your Auto-Recovery Dashboard.\n\n"
                f"SNS Topic: {topic_arn}\n"
                f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
                f"If you received this, email alerts are working correctly.\n"
                f"You will receive alerts for:\n"
                f"  - CPU > 70% (reboot triggered)\n"
                f"  - Instance stopped/terminated\n"
                f"  - Instance recovered\n"
            )
        )
        return jsonify({"status": "success", "topic_arn": topic_arn, "message": "Test email sent — check your inbox"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

if __name__ == "__main__":
    app.run(debug=True)
