import boto3
import time

REGION = "us-west-1"
ec2 = boto3.client("ec2", region_name=REGION)
lambda_client = boto3.client("lambda", region_name=REGION)
iam = boto3.client("iam")

print("🛑 Stopping demo instances...")

response = ec2.describe_instances(
    Filters=[
        {"Name": "tag:Project", "Values": ["auto-recovery"]},
        {"Name": "instance-state-name", "Values": ["running"]}
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
        print(f"  Stopping: {name} ({i['InstanceId']})")

if not instance_ids:
    print("⚠️  No running instances found!")
    print("   Either already stopped or not created yet")
else:
    ec2.stop_instances(InstanceIds=instance_ids)
    print(f"\n⏳ Waiting for {len(instance_ids)} instances to stop...")
    time.sleep(10)

    response = ec2.describe_instances(InstanceIds=instance_ids)
    print("\n✅ Instance Status:")
    for r in response["Reservations"]:
        for i in r["Instances"]:
            name = "unnamed"
            for tag in i.get("Tags", []):
                if tag["Key"] == "Name":
                    name = tag["Value"]
            state = i["State"]["Name"]
            emoji = "🔴" if state == "stopped" else "🟡"
            print(f"   {emoji} {name} → {state}")

# ─── CLEANUP LAMBDA ───────────────────────────────────
print("\n⚡ Cleaning up Lambda Function...")
FUNCTION_NAME = "CloudAutoRecoveryFunction"
try:
    lambda_client.delete_function(FunctionName=FUNCTION_NAME)
    print(f"  ✅ Lambda function '{FUNCTION_NAME}' deleted")
except lambda_client.exceptions.ResourceNotFoundException:
    print("  ℹ️  Lambda function not found — skipping")
except Exception as e:
    print(f"  ⚠️  Lambda: {e}")

# ─── CLEANUP IAM ROLE ─────────────────────────────────
print("\n🔐 Cleaning up IAM Role...")
ROLE_NAME = "CloudAutoRecoveryLambdaRole"
try:
    policies = iam.list_role_policies(RoleName=ROLE_NAME).get("PolicyNames", [])
    for policy_name in policies:
        iam.delete_role_policy(RoleName=ROLE_NAME, PolicyName=policy_name)
        print(f"  🗑️  Deleted inline policy: {policy_name}")
    iam.delete_role(RoleName=ROLE_NAME)
    print(f"  ✅ IAM role '{ROLE_NAME}' deleted")
except iam.exceptions.NoSuchEntityException:
    print("  ℹ️  IAM role not found — skipping")
except Exception as e:
    print(f"  ⚠️  IAM: {e}")

print("\n✅ Stop complete!")
