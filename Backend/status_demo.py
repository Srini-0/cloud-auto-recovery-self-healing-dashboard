import boto3

REGION = "us-west-1"
ec2 = boto3.client("ec2", region_name=REGION)

print("📊 Checking demo instance status...")

response = ec2.describe_instances(
    Filters=[
        {"Name": "tag:Project", "Values": ["auto-recovery"]}
    ]
)

instances = []
for r in response["Reservations"]:
    for i in r["Instances"]:
        name = "unnamed"
        for tag in i.get("Tags", []):
            if tag["Key"] == "Name":
                name = tag["Value"]
        instances.append((name, i["InstanceId"], i["State"]["Name"]))

if not instances:
    print("⚠️  No instances found with tag Project: auto-recovery")
else:
    print("\n✅ Instance Status:")
    for name, instance_id, state in instances:
        if state == "running":
            emoji = "🟢"
        elif state == "stopped":
            emoji = "🔴"
        else:
            emoji = "🟡"
        print(f"   {emoji} {name} | {instance_id} | {state}")
