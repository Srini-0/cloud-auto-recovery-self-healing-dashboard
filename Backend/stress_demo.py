"""
stress_demo.py — Trigger CPU stress on demo instances via SSM (no SSH key needed).
Uses AWS Systems Manager Run Command so instances don't need a public IP or open port 22.

Requirements:
  - Instances must have SSM Agent running (pre-installed on Amazon Linux 2/2023, Ubuntu 20.04+)
  - Instance IAM role must have AmazonSSMManagedInstanceCore policy attached
  - pip install boto3
"""

import boto3
import time
import sys

REGION = "us-west-1"

ec2 = boto3.client("ec2", region_name=REGION)
ssm = boto3.client("ssm", region_name=REGION)

# ─── HELPERS ────────────────────────────────────────────────────────────────

def get_project_instances(state_filter=None):
    filters = [{"Name": "tag:Project", "Values": ["auto-recovery"]}]
    if state_filter:
        filters.append({"Name": "instance-state-name", "Values": state_filter})
    response = ec2.describe_instances(Filters=filters)
    instances = []
    for r in response["Reservations"]:
        for i in r["Instances"]:
            name = next((t["Value"] for t in i.get("Tags", []) if t["Key"] == "Name"), "unnamed")
            instances.append({
                "id": i["InstanceId"],
                "name": name,
                "state": i["State"]["Name"],
            })
    return instances


def run_ssm_command(instance_id, commands, comment="stress-demo"):
    """Send shell commands to an instance via SSM Run Command."""
    try:
        response = ssm.send_command(
            InstanceIds=[instance_id],
            DocumentName="AWS-RunShellScript",
            Parameters={"commands": commands},
            Comment=comment,
            TimeoutSeconds=60,
        )
        command_id = response["Command"]["CommandId"]
        return command_id
    except Exception as e:
        print(f"  ❌ SSM error on {instance_id}: {e}")
        return None


def wait_for_command(command_id, instance_id, timeout=30):
    """Poll until SSM command finishes or times out."""
    for _ in range(timeout // 2):
        time.sleep(2)
        try:
            result = ssm.get_command_invocation(
                CommandId=command_id,
                InstanceId=instance_id,
            )
            status = result["Status"]
            if status in ("Success", "Failed", "Cancelled", "TimedOut"):
                return status, result.get("StandardOutputContent", ""), result.get("StandardErrorContent", "")
        except ssm.exceptions.InvocationDoesNotExist:
            pass
    return "Timeout", "", ""


# ─── ACTIONS ────────────────────────────────────────────────────────────────

def install_stress(instance_id, instance_name):
    """Install stress / stress-ng if not already present."""
    print(f"  📦 Installing stress on {instance_name} ({instance_id})...")
    cmd_id = run_ssm_command(
        instance_id,
        [
            "which stress-ng && echo 'already installed' && exit 0",
            "yum install -y stress stress-ng 2>/dev/null || apt-get install -y -q stress stress-ng 2>/dev/null",
            "echo 'install done'",
        ],
        comment="install-stress",
    )
    if cmd_id:
        status, out, err = wait_for_command(cmd_id, instance_id, timeout=60)
        if status == "Success":
            print(f"  ✅ stress tools ready on {instance_name}")
        else:
            print(f"  ⚠️  Install status: {status} — {err.strip()[:120]}")


def start_stress(instance_id, instance_name, duration=300, cpu_workers=0):
    """
    Spike CPU to ~100% for `duration` seconds.
    cpu_workers=0 means use all available vCPUs.
    """
    print(f"  🔥 Starting CPU stress on {instance_name} ({instance_id}) for {duration}s...")
    workers = cpu_workers if cpu_workers > 0 else "$(nproc)"
    cmd_id = run_ssm_command(
        instance_id,
        [
            # Kill any existing stress processes first
            "pkill -f stress-ng 2>/dev/null; pkill -f stress 2>/dev/null; sleep 1",
            f"nohup stress-ng --cpu {workers} --timeout {duration}s --metrics-brief > /tmp/stress.log 2>&1 &",
            "echo 'stress started'",
        ],
        comment="start-stress",
    )
    if cmd_id:
        status, out, _ = wait_for_command(cmd_id, instance_id)
        if status == "Success":
            print(f"  ✅ Stress running — CPU will spike for {duration}s")
        else:
            print(f"  ⚠️  Stress start status: {status}")


def stop_stress(instance_id, instance_name):
    """Kill stress processes on the instance."""
    print(f"  🛑 Stopping stress on {instance_name} ({instance_id})...")
    cmd_id = run_ssm_command(
        instance_id,
        ["pkill -f stress-ng 2>/dev/null; pkill -f stress 2>/dev/null; echo 'stopped'"],
        comment="stop-stress",
    )
    if cmd_id:
        status, _, _ = wait_for_command(cmd_id, instance_id)
        print(f"  ✅ Stress stopped ({status})")


# ─── MENU ───────────────────────────────────────────────────────────────────

def main():
    print("\n🔥 Stress Demo Tool")
    print("=" * 50)

    instances = get_project_instances(state_filter=["running"])
    if not instances:
        print("❌ No running project instances found.")
        print("   Run start_demo.py first.")
        sys.exit(1)

    print("\nRunning instances:")
    for idx, inst in enumerate(instances):
        print(f"  [{idx + 1}] {inst['name']} ({inst['id']})")

    print("\nOptions:")
    print("  [a] Stress ALL instances")
    print("  [s] Stress a SINGLE instance")
    print("  [x] STOP stress on all instances")
    print("  [i] Install stress tools on all instances")
    print("  [q] Quit")

    choice = input("\nChoice: ").strip().lower()

    if choice == "q":
        sys.exit(0)

    elif choice == "i":
        for inst in instances:
            install_stress(inst["id"], inst["name"])

    elif choice == "x":
        for inst in instances:
            stop_stress(inst["id"], inst["name"])
        print("\n✅ All stress processes stopped.")

    elif choice == "a":
        duration = input("Duration in seconds [default 300]: ").strip()
        duration = int(duration) if duration.isdigit() else 300
        for inst in instances:
            install_stress(inst["id"], inst["name"])
            start_stress(inst["id"], inst["name"], duration=duration)
        print(f"\n✅ Stressing all {len(instances)} instances for {duration}s")
        print("   Watch the CPU chart on your dashboard spike up!")

    elif choice == "s":
        for idx, inst in enumerate(instances):
            print(f"  [{idx + 1}] {inst['name']}")
        pick = input("Select instance number: ").strip()
        if not pick.isdigit() or not (1 <= int(pick) <= len(instances)):
            print("Invalid selection.")
            sys.exit(1)
        inst = instances[int(pick) - 1]
        duration = input("Duration in seconds [default 300]: ").strip()
        duration = int(duration) if duration.isdigit() else 300
        install_stress(inst["id"], inst["name"])
        start_stress(inst["id"], inst["name"], duration=duration)
        print(f"\n✅ Stressing {inst['name']} for {duration}s")
        print("   Watch the CPU chart on your dashboard!")

    else:
        print("Unknown option.")


if __name__ == "__main__":
    main()
