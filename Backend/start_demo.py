import boto3
import time

REGION = "us-west-1"
ec2 = boto3.client("ec2", region_name=REGION)

print("🚀 Starting demo instances...")

# Get all project instances
response = ec2.describe_instances(
    Filters=[
        {
            "Name": "tag:Project",
            "Values": ["auto-recovery"]
        },
        {
            "Name": "instance-state-name",
            "Values": ["stopped"]
        }
    ]
)

instance_ids = []
for r in response["Reservations"]:
    for i in r["Instances"]:
        name = "unnamed"
        for tag in i.get("Tags", []):
            if tag["Key"] == "Name":
                name = tag["Value"]
        instance_ids.append(i["InstanceId"])
        print(f"  Starting: {name} ({i['InstanceId']})")

if not instance_ids:
    print("⚠️  No stopped instances found!")
    print("   Either already running or not created yet")
else:
    ec2.start_instances(InstanceIds=instance_ids)
    print(f"\n⏳ Waiting for {len(instance_ids)} instances to start...")
    time.sleep(20)

    # Show final status
    response = ec2.describe_instances(InstanceIds=instance_ids)
    print("\n✅ Instance Status:")
    for r in response["Reservations"]:
        for i in r["Instances"]:
            name = "unnamed"
            for tag in i.get("Tags", []):
                if tag["Key"] == "Name":
                    name = tag["Value"]
            state = i["State"]["Name"]
            emoji = "🟢" if state == "running" else "🟡"
            print(f"   {emoji} {name} → {state}")

print("\n🎯 Dashboard: http://localhost:5173")
print("✅ Demo ready!")