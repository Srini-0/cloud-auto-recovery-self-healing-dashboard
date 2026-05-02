"""
Demo scenario runner — stress, terminate, and recover instances.

Usage:
  python3 scenario_demo.py stress     # spike CPU on prod-server-3
  python3 scenario_demo.py terminate  # terminate prod-server-4
  python3 scenario_demo.py recover    # reboot prod-server-4 (or start if stopped)
  python3 scenario_demo.py status     # show all instance states
"""

import boto3
import sys
import time

REGION = "us-west-1"
ec2 = boto3.client("ec2", region_name=REGION)
ssm = boto3.client("ssm", region_name=REGION)

STATE_EMOJI = {"running": "🟢", "stopped": "🔴", "terminated": "⚫", "stopping": "🟡", "pending": "🟡"}


def get_demo_instances():
    response = ec2.describe_instances(
        Filters=[{"Name": "tag:Project", "Values": ["auto-recovery"]}]
    )
    instances = {}
    for r in response["Reservations"]:
        for i in r["Instances"]:
            name = next((t["Value"] for t in i.get("Tags", []) if t["Key"] == "Name"), "unnamed")
            instances[name] = {
                "id": i["InstanceId"],
                "state": i["State"]["Name"],
                "ip": i.get("PublicIpAddress", "N/A")
            }
    return instances


def show_status(instances):
    print("\n📊 Current Instance Status:")
    for name, info in instances.items():
        emoji = STATE_EMOJI.get(info["state"], "⚪")
        print(f"   {emoji} {name:<20} {info['id']}   {info['state']:<12}  IP: {info['ip']}")
    print()


def stress(instances):
    """Stress prod-server-3 via SSM to spike CPU."""
    target = instances.get("prod-server-3")
    if not target:
        print("❌ prod-server-3 not found.")
        return
    if target["state"] != "running":
        print(f"⚠️  prod-server-3 is {target['state']}, must be running to stress.")
        return

    instance_id = target["id"]
    print(f"🔥 Stressing prod-server-3 ({instance_id}) via SSM...")
    print("   This will spike CPU above 70% to trigger the CloudWatch alarm.\n")

    try:
        response = ssm.send_command(
            InstanceIds=[instance_id],
            DocumentName="AWS-RunShellScript",
            Parameters={"commands": ["stress-ng --cpu 2 --timeout 120s &"]},
            Comment="Demo CPU stress"
        )
        cmd_id = response["Command"]["CommandId"]
        print(f"✅ Stress command sent (CommandId: {cmd_id})")
        print("   CPU will spike for ~2 minutes.")
        print("   Watch the dashboard → CloudWatch alarms should trigger.")
    except ssm.exceptions.InvalidInstanceId:
        print("⚠️  SSM not available on this instance.")
        print("   To stress manually, SSH in and run:")
        print(f"      ssh ec2-user@{target['ip']}")
        print("      stress-ng --cpu 2 --timeout 120s &")
        print("   Or use the simpler: dd if=/dev/zero of=/dev/null &")


def terminate(instances):
    """Terminate prod-server-4 to simulate a crash."""
    target = instances.get("prod-server-4")
    if not target:
        print("❌ prod-server-4 not found.")
        return
    if target["state"] == "terminated":
        print("⚠️  prod-server-4 is already terminated.")
        return

    instance_id = target["id"]
    print(f"💀 Terminating prod-server-4 ({instance_id})...")
    confirm = input("   Are you sure? This cannot be undone. (yes/no): ").strip().lower()
    if confirm != "yes":
        print("   Cancelled.")
        return

    ec2.terminate_instances(InstanceIds=[instance_id])
    print("✅ Termination triggered.")
    print("   Watch the dashboard — instance will show as 'terminated'.")
    print("   If ASG is configured, a replacement will launch automatically.")


def recover(instances):
    """Reboot or start prod-server-4 to show recovery."""
    target = instances.get("prod-server-4")
    if not target:
        print("❌ prod-server-4 not found.")
        return

    instance_id = target["id"]
    state = target["state"]

    if state == "terminated":
        print("⚠️  prod-server-4 is terminated — cannot recover a terminated instance.")
        print("   If ASG is set up, it will launch a replacement automatically.")
        return
    elif state == "stopped":
        print(f"🔄 Starting prod-server-4 ({instance_id})...")
        ec2.start_instances(InstanceIds=[instance_id])
        print("✅ Start triggered. Watch the dashboard for recovery.")
    elif state == "running":
        print(f"🔄 Rebooting prod-server-4 ({instance_id}) to simulate recovery...")
        ec2.reboot_instances(InstanceIds=[instance_id])
        print("✅ Reboot triggered.")
        print("   Instance will briefly go offline then come back — shows recovery flow.")
    else:
        print(f"⚠️  Instance is in state '{state}', try again shortly.")


# ─── MAIN ────────────────────────────────────────────

if len(sys.argv) < 2:
    print(__doc__)
    sys.exit(0)

cmd = sys.argv[1].lower()
instances = get_demo_instances()

if not instances:
    print("⚠️  No demo instances found. Run demo_setup.py first.")
    sys.exit(1)

show_status(instances)

if cmd == "stress":
    stress(instances)
elif cmd == "terminate":
    terminate(instances)
elif cmd == "recover":
    recover(instances)
elif cmd == "status":
    pass  # already printed above
else:
    print(f"❌ Unknown command: {cmd}")
    print(__doc__)
