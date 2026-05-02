import boto3
import time

REGION = "us-west-1"

ec2 = boto3.client("ec2", region_name=REGION)
cloudwatch = boto3.client("cloudwatch", region_name=REGION)
autoscaling = boto3.client("autoscaling", region_name=REGION)
sns = boto3.client("sns", region_name=REGION)
lambda_client = boto3.client("lambda", region_name=REGION)
iam = boto3.client("iam")

print("🧹 Starting full cleanup...")
print("=" * 50)

# ─── STEP 1: DELETE AUTO SCALING GROUPS ──────────────
print("\n⚖️  Step 1: Deleting Auto Scaling Groups...")
try:
    all_asgs = autoscaling.describe_auto_scaling_groups().get("AutoScalingGroups", [])
    project_asgs = [
        asg["AutoScalingGroupName"] for asg in all_asgs
        if any(t.get("Key") == "Project" and t.get("Value") == "auto-recovery"
               for t in asg.get("Tags", []))
        or "auto-recovery" in asg["AutoScalingGroupName"].lower()
    ]

    if not project_asgs:
        print("  ℹ️  No matching ASGs found")
    else:
        for asg_name in project_asgs:
            try:
                autoscaling.update_auto_scaling_group(
                    AutoScalingGroupName=asg_name,
                    MinSize=0, MaxSize=0, DesiredCapacity=0
                )
                print(f"  ⏳ Scaling down: {asg_name}")
            except Exception as e:
                print(f"  ⚠️  Scale down {asg_name}: {e}")

        print("  ⏳ Waiting 20s for instances to terminate...")
        time.sleep(20)

        for asg_name in project_asgs:
            try:
                autoscaling.delete_auto_scaling_group(
                    AutoScalingGroupName=asg_name, ForceDelete=True
                )
                print(f"  ✅ Deleted ASG: {asg_name}")
            except Exception as e:
                print(f"  ⚠️  Delete {asg_name}: {e}")
except Exception as e:
    print(f"  ⚠️  ASG: {e}")

# ─── STEP 2: DELETE LAUNCH TEMPLATES ─────────────────
print("\n📋 Step 2: Deleting Launch Templates...")
try:
    templates = ec2.describe_launch_templates().get("LaunchTemplates", [])
    project_templates = [
        t["LaunchTemplateName"] for t in templates
        if "auto-recovery" in t["LaunchTemplateName"].lower()
    ]
    if not project_templates:
        print("  ℹ️  No matching launch templates found")
    else:
        for name in project_templates:
            try:
                ec2.delete_launch_template(LaunchTemplateName=name)
                print(f"  ✅ Deleted launch template: {name}")
            except Exception as e:
                print(f"  ⚠️  {name}: {e}")
except Exception as e:
    print(f"  ⚠️  Launch Templates: {e}")

# ─── STEP 3: TERMINATE EC2 INSTANCES ─────────────────
print("\n🖥️  Step 3: Terminating EC2 instances...")
try:
    response = ec2.describe_instances(
        Filters=[
            {"Name": "tag:Project", "Values": ["auto-recovery"]},
            {"Name": "instance-state-name", "Values": ["running", "stopped", "stopping", "pending"]}
        ]
    )
    instance_ids = []
    for r in response["Reservations"]:
        for i in r["Instances"]:
            name = next((t["Value"] for t in i.get("Tags", []) if t["Key"] == "Name"), "unnamed")
            instance_ids.append(i["InstanceId"])
            print(f"  🔴 Terminating: {name} ({i['InstanceId']})")

    if instance_ids:
        ec2.terminate_instances(InstanceIds=instance_ids)
        print(f"  ✅ Termination requested for {len(instance_ids)} instance(s)")
    else:
        print("  ℹ️  No instances found to terminate")
except Exception as e:
    print(f"  ⚠️  EC2: {e}")

# ─── STEP 4: DELETE CLOUDWATCH ALARMS ────────────────
print("\n🔔 Step 4: Deleting CloudWatch Alarms...")
try:
    # Collect all project instance IDs and names for matching
    all_instances = ec2.describe_instances(
        Filters=[{"Name": "tag:Project", "Values": ["auto-recovery"]}]
    )
    project_ids = set()
    project_names = set()
    for r in all_instances.get("Reservations", []):
        for i in r["Instances"]:
            project_ids.add(i["InstanceId"])
            name = next((t["Value"] for t in i.get("Tags", []) if t["Key"] == "Name"), "")
            if name:
                project_names.add(name)

    paginator = cloudwatch.get_paginator("describe_alarms")
    alarm_names = []
    for page in paginator.paginate():
        for alarm in page["MetricAlarms"]:
            alarm_name = alarm["AlarmName"]
            dims = {d["Name"]: d["Value"] for d in alarm.get("Dimensions", [])}
            instance_id = dims.get("InstanceId", "")
            # Match by instance ID, instance name in alarm name, or known prefixes
            if (instance_id in project_ids
                    or any(n in alarm_name for n in project_names)
                    or any(alarm_name.startswith(p) for p in [
                        "HighCPU-", "StatusCheck-", "auto-recovery"
                    ])):
                alarm_names.append(alarm_name)

    if alarm_names:
        for i in range(0, len(alarm_names), 100):
            cloudwatch.delete_alarms(AlarmNames=alarm_names[i:i+100])
        print(f"  ✅ Deleted {len(alarm_names)} alarm(s)")
    else:
        print("  ℹ️  No matching alarms found")
except Exception as e:
    print(f"  ⚠️  CloudWatch: {e}")

# ─── STEP 5: DELETE SNS TOPIC ─────────────────────────
print("\n📧 Step 5: Deleting SNS Topic...")
try:
    topics = sns.list_topics().get("Topics", [])
    deleted = 0
    for t in topics:
        arn = t["TopicArn"]
        if "CloudAutoRecoveryAlerts" in arn:
            sns.delete_topic(TopicArn=arn)
            print(f"  ✅ Deleted SNS topic: {arn}")
            deleted += 1
    if not deleted:
        print("  ℹ️  No matching SNS topic found")
except Exception as e:
    print(f"  ⚠️  SNS: {e}")

# ─── STEP 6: DELETE LAMBDA FUNCTION ──────────────────
print("\n⚡ Step 6: Deleting Lambda Function...")
FUNCTION_NAME = "CloudAutoRecoveryFunction"
try:
    lambda_client.delete_function(FunctionName=FUNCTION_NAME)
    print(f"  ✅ Lambda function '{FUNCTION_NAME}' deleted")
except lambda_client.exceptions.ResourceNotFoundException:
    print("  ℹ️  Lambda function not found — skipping")
except Exception as e:
    print(f"  ⚠️  Lambda: {e}")

# ─── STEP 7: DELETE IAM ROLE ──────────────────────────
print("\n🔐 Step 7: Deleting IAM Role...")
ROLE_NAME = "CloudAutoRecoveryLambdaRole"
try:
    # Detach managed policies first
    attached = iam.list_attached_role_policies(RoleName=ROLE_NAME).get("AttachedPolicies", [])
    for p in attached:
        iam.detach_role_policy(RoleName=ROLE_NAME, PolicyArn=p["PolicyArn"])
        print(f"  🗑️  Detached managed policy: {p['PolicyName']}")
    # Delete inline policies
    inline = iam.list_role_policies(RoleName=ROLE_NAME).get("PolicyNames", [])
    for policy_name in inline:
        iam.delete_role_policy(RoleName=ROLE_NAME, PolicyName=policy_name)
        print(f"  🗑️  Deleted inline policy: {policy_name}")
    iam.delete_role(RoleName=ROLE_NAME)
    print(f"  ✅ IAM role '{ROLE_NAME}' deleted")
except iam.exceptions.NoSuchEntityException:
    print("  ℹ️  IAM role not found — skipping")
except Exception as e:
    print(f"  ⚠️  IAM: {e}")

# ─── DONE ─────────────────────────────────────────────
print("\n" + "=" * 50)
print("✅ Full cleanup complete!")
print("   ASG · Launch Template · EC2 · CloudWatch · SNS · Lambda · IAM")
print("=" * 50)
