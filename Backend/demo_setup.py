import boto3
import time
import subprocess
from datetime import datetime

REGION = "us-west-1"
EMAIL = input("Enter your email for SNS alerts: ")

ec2 = boto3.client("ec2", region_name=REGION)
iam = boto3.client("iam", region_name=REGION)
autoscaling = boto3.client("autoscaling", region_name=REGION)
cloudwatch = boto3.client("cloudwatch", region_name=REGION)
sns = boto3.client("sns", region_name=REGION)

print("\n🚀 Starting Complete Demo Setup...")
print("="*50)

# ─── STEP 1: SNS TOPIC ───────────────────────────────
print("\n📧 Step 1: Setting up SNS Email Alerts...")
try:
    topic = sns.create_topic(Name="CloudAutoRecoveryAlerts")
    TOPIC_ARN = topic["TopicArn"]
    
    sns.subscribe(
        TopicArn=TOPIC_ARN,
        Protocol="email",
        Endpoint=EMAIL
    )
    print(f"✅ SNS Topic created: {TOPIC_ARN}")
    print(f"✅ Confirmation email sent to {EMAIL}")
    print("⚠️  CHECK YOUR EMAIL NOW and click CONFIRM SUBSCRIPTION!")
    input("\nPress Enter after confirming email subscription...")
except Exception as e:
    print(f"⚠️  SNS error: {e}")
    TOPIC_ARN = None

# ─── STEP 1b: CREATE SSM IAM ROLE ────────────────────
print("\n🔐 Step 1b: Setting up SSM IAM Role...")
INSTANCE_PROFILE_NAME = "auto-recovery-ssm-profile"
ROLE_NAME = "auto-recovery-ssm-role"

try:
    iam.create_role(
        RoleName=ROLE_NAME,
        AssumeRolePolicyDocument='{"Version":"2012-10-17","Statement":[{"Effect":"Allow","Principal":{"Service":"ec2.amazonaws.com"},"Action":"sts:AssumeRole"}]}',
        Description="SSM role for auto-recovery demo"
    )
    iam.attach_role_policy(
        RoleName=ROLE_NAME,
        PolicyArn="arn:aws:iam::aws:policy/AmazonSSMManagedInstanceCore"
    )
    print(f"  ✅ IAM Role created: {ROLE_NAME}")
except iam.exceptions.EntityAlreadyExistsException:
    print(f"  ✅ IAM Role already exists: {ROLE_NAME}")

try:
    iam.create_instance_profile(InstanceProfileName=INSTANCE_PROFILE_NAME)
    iam.add_role_to_instance_profile(
        InstanceProfileName=INSTANCE_PROFILE_NAME,
        RoleName=ROLE_NAME
    )
    print(f"  ✅ Instance Profile created: {INSTANCE_PROFILE_NAME}")
    print("  ⏳ Waiting for profile to propagate...")
    time.sleep(15)
except iam.exceptions.EntityAlreadyExistsException:
    print(f"  ✅ Instance Profile already exists: {INSTANCE_PROFILE_NAME}")

# ─── STEP 2: GET AMI FROM EXISTING INSTANCE ──────────
print("\n🔍 Step 2: Getting existing instance details...")
try:
    response = ec2.describe_instances(
        Filters=[{
            "Name": "instance-state-name",
            "Values": ["running", "stopped"]
        }]
    )
    
    existing = None
    for r in response["Reservations"]:
        for i in r["Instances"]:
            existing = i
            break
        if existing:
            break
    
    if existing:
        AMI_ID = existing["ImageId"]
        INSTANCE_TYPE = "t2.micro"
        SUBNET_ID = existing["SubnetId"]
        SG_IDS = [sg["GroupId"] for sg in existing["SecurityGroups"]]
        print(f"✅ Using AMI: {AMI_ID}")
        print(f"✅ Subnet: {SUBNET_ID}")
    else:
        print("❌ No existing instances found!")
        exit()
except Exception as e:
    print(f"❌ Error: {e}")
    exit()

# ─── STEP 3: CREATE 4 DEMO INSTANCES ─────────────────
print("\n🖥️  Step 3: Creating 4 demo instances...")

instance_configs = [
    {"name": "prod-server-1", "role": "healthy"},
    {"name": "prod-server-2", "role": "healthy"},
    {"name": "prod-server-3", "role": "unhealthy"},
    {"name": "prod-server-4", "role": "recovering"},
]

created_instances = []

USER_DATA_SCRIPT = """#!/bin/bash
# Install stress tools on first boot
yum install -y stress stress-ng 2>/dev/null || apt-get install -y stress stress-ng 2>/dev/null
echo "stress tools installed" >> /var/log/demo-setup.log
"""

import base64
USER_DATA_B64 = base64.b64encode(USER_DATA_SCRIPT.encode()).decode()

for config in instance_configs:
    try:
        response = ec2.run_instances(
            ImageId=AMI_ID,
            InstanceType=INSTANCE_TYPE,
            MinCount=1,
            MaxCount=1,
            SubnetId=SUBNET_ID,
            SecurityGroupIds=SG_IDS,
            UserData=USER_DATA_B64,
            IamInstanceProfile={"Name": INSTANCE_PROFILE_NAME},
            TagSpecifications=[{
                "ResourceType": "instance",
                "Tags": [
                    {"Key": "Name", "Value": config["name"]},
                    {"Key": "Role", "Value": config["role"]},
                    {"Key": "Project", "Value": "auto-recovery"}
                ]
            }]
        )
        
        instance_id = response["Instances"][0]["InstanceId"]
        created_instances.append({
            "id": instance_id,
            "name": config["name"],
            "role": config["role"]
        })
        print(f"  ✅ Created {config['name']} ({instance_id})")
        
    except Exception as e:
        print(f"  ❌ Failed to create {config['name']}: {e}")

print(f"\n✅ Created {len(created_instances)} instances")
print("⏳ Waiting 30 seconds for instances to start...")
time.sleep(30)

# ─── STEP 4: WAIT FOR RUNNING STATE ──────────────────
print("\n⏳ Step 4: Waiting for all instances to be running...")
all_ids = [i["id"] for i in created_instances]

for attempt in range(12):
    response = ec2.describe_instances(InstanceIds=all_ids)
    states = []
    for r in response["Reservations"]:
        for i in r["Instances"]:
            states.append(i["State"]["Name"])
    
    running = states.count("running")
    print(f"  Running: {running}/{len(all_ids)}")
    
    if running == len(all_ids):
        print("✅ All instances running!")
        break
    time.sleep(10)

# ─── STEP 5: CREATE CLOUDWATCH ALARMS ────────────────
print("\n🔔 Step 5: Creating CloudWatch Alarms...")

for instance in created_instances:
    try:
        # CPU Alarm
        alarm_actions = [TOPIC_ARN] if TOPIC_ARN else []
        
        cloudwatch.put_metric_alarm(
            AlarmName=f"HighCPU-{instance['name']}",
            ComparisonOperator="GreaterThanThreshold",
            EvaluationPeriods=1,
            MetricName="CPUUtilization",
            Namespace="AWS/EC2",
            Period=60,
            Statistic="Average",
            Threshold=70.0,
            ActionsEnabled=True,
            AlarmActions=alarm_actions,
            AlarmDescription=f"CPU above 70% on {instance['name']}",
            Dimensions=[{
                "Name": "InstanceId",
                "Value": instance["id"]
            }]
        )
        
        # Status Check Alarm
        cloudwatch.put_metric_alarm(
            AlarmName=f"StatusCheck-{instance['name']}",
            ComparisonOperator="GreaterThanThreshold",
            EvaluationPeriods=2,
            MetricName="StatusCheckFailed",
            Namespace="AWS/EC2",
            Period=60,
            Statistic="Maximum",
            Threshold=0,
            ActionsEnabled=True,
            AlarmActions=alarm_actions,
            AlarmDescription=f"Status check failed on {instance['name']}",
            Dimensions=[{
                "Name": "InstanceId",
                "Value": instance["id"]
            }]
        )
        print(f"  ✅ Alarms created for {instance['name']}")
        
    except Exception as e:
        print(f"  ⚠️  Alarm error for {instance['name']}: {e}")

# ─── STEP 6: AUTO SCALING GROUP ──────────────────────
print("\n⚖️  Step 6: Creating Auto Scaling Group...")
try:
    lt = ec2.create_launch_template(
        LaunchTemplateName="auto-recovery-demo-template",
        LaunchTemplateData={
            "ImageId": AMI_ID,
            "InstanceType": INSTANCE_TYPE,
            "SecurityGroupIds": SG_IDS,
            "UserData": USER_DATA_B64,
            "TagSpecifications": [{
                "ResourceType": "instance",
                "Tags": [
                    {"Key": "Name", "Value": "asg-auto-recovery"},
                    {"Key": "Project", "Value": "auto-recovery"}
                ]
            }]
        }
    )
    LT_ID = lt["LaunchTemplate"]["LaunchTemplateId"]
    print(f"  ✅ Launch Template created: {LT_ID}")
except Exception as e:
    if "already exists" in str(e).lower():
        lt = ec2.describe_launch_templates(
            LaunchTemplateNames=["auto-recovery-demo-template"]
        )
        LT_ID = lt["LaunchTemplates"][0]["LaunchTemplateId"]
        print(f"  ✅ Using existing Launch Template: {LT_ID}")
    else:
        print(f"  ⚠️  Launch Template error: {e}")
        LT_ID = None

if LT_ID:
    try:
        autoscaling.create_auto_scaling_group(
            AutoScalingGroupName="auto-recovery-demo-asg",
            LaunchTemplate={
                "LaunchTemplateId": LT_ID,
                "Version": "$Latest"
            },
            MinSize=1,
            MaxSize=4,
            DesiredCapacity=2,
            AvailabilityZones=["us-west-1a", "us-west-1c"],
            HealthCheckType="EC2",
            HealthCheckGracePeriod=60,
            Tags=[{
                "Key": "Name",
                "Value": "asg-auto-recovery",
                "PropagateAtLaunch": True
            }]
        )
        print("  ✅ Auto Scaling Group created!")
        print("     Min:1 | Desired:2 | Max:4")

        if TOPIC_ARN:
            autoscaling.put_notification_configuration(
                AutoScalingGroupName="auto-recovery-demo-asg",
                TopicARN=TOPIC_ARN,
                NotificationTypes=[
                    "autoscaling:EC2_INSTANCE_LAUNCH",
                    "autoscaling:EC2_INSTANCE_TERMINATE",
                    "autoscaling:EC2_INSTANCE_LAUNCH_ERROR"
                ]
            )
            print("  ✅ ASG notifications connected to SNS")

    except Exception as e:
        if "AlreadyExists" in str(e):
            print("  ✅ Auto Scaling Group already exists")
        else:
            print(f"  ⚠️  ASG error: {e}")

# ─── STEP 7: DEMO SCENARIO SETUP ─────────────────────
print("\n🎭 Step 7: Setting up demo scenarios...")

# Find prod-server-3 (unhealthy demo)
unhealthy_instance = next(
    (i for i in created_instances if i["role"] == "unhealthy"), None
)
recovering_instance = next(
    (i for i in created_instances if i["role"] == "recovering"), None
)

if unhealthy_instance:
    print(f"\n  📌 To trigger UNHEALTHY demo:")
    print(f"     SSH into {unhealthy_instance['name']}")
    print(f"     Instance ID: {unhealthy_instance['id']}")
    print(f"     Run: dd if=/dev/zero of=/dev/null &")
    print(f"     This will spike CPU above 70%")

if recovering_instance:
    print(f"\n  📌 To trigger RECOVERING demo:")
    print(f"     Instance ID: {recovering_instance['id']}")
    print(f"     We will reboot it to show recovery")

# ─── STEP 8: SEND SETUP COMPLETE EMAIL ───────────────
if TOPIC_ARN:
    print("\n📨 Step 8: Sending setup complete notification...")
    try:
        instance_summary = "\n".join([
            f"  - {i['name']} ({i['id']}): {i['role'].upper()}"
            for i in created_instances
        ])
        
        sns.publish(
            TopicArn=TOPIC_ARN,
            Subject="🚀 Cloud Auto-Recovery Demo Setup Complete",
            Message=f"""
Cloud Auto-Recovery System - Demo Ready!

Instances Created:
{instance_summary}

Setup Complete:
✅ CloudWatch Alarms: Active for all instances
✅ Auto Scaling Group: Running (Min:1, Max:4)  
✅ SNS Alerts: Sending to {EMAIL}

Demo Scenarios Ready:
🟢 prod-server-1: HEALTHY
🟢 prod-server-2: HEALTHY  
🔴 prod-server-3: Stress to make UNHEALTHY
🔄 prod-server-4: Reboot to show RECOVERING

Dashboard: http://localhost:5173

Time: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
            """
        )
        print(f"✅ Setup complete email sent to {EMAIL}")
    except Exception as e:
        print(f"⚠️  Email error: {e}")

# ─── DONE ─────────────────────────────────────────────
print("\n" + "="*50)
print("🎉 COMPLETE DEMO SETUP DONE!")
print("="*50)
print(f"\n📊 Dashboard: http://localhost:5173")
print(f"📧 Alerts: {EMAIL}")
print(f"\n🖥️  Your 4 Demo Instances:")
for i in created_instances:
    emoji = "🟢" if i["role"] == "healthy" else "🔴" if i["role"] == "unhealthy" else "🔄"
    print(f"   {emoji} {i['name']} ({i['id']})")

print(f"\n🎭 Demo Flow:")
print("   1. Show dashboard with 4 instances")
print("   2. SSH into prod-server-3 and run:")
print("      dd if=/dev/zero of=/dev/null &")
print("   3. Watch CPU spike → alarm triggers → email arrives")
print("   4. Auto-heal reboots it → recovery shows on dashboard")
print("   5. Instance recovers → back to healthy")
print("\n✅ Ready for review demo!")
print("="*50)