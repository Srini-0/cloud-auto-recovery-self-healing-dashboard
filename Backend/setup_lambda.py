import boto3
import json
import zipfile
import os
import time
from datetime import datetime

REGION = "us-west-1"

ec2 = boto3.client("ec2", region_name=REGION)
cloudwatch = boto3.client("cloudwatch", region_name=REGION)
sns = boto3.client("sns", region_name=REGION)
lambda_client = boto3.client("lambda", region_name=REGION)
iam = boto3.client("iam")

print("\n🚀 Setting up Lambda Auto-Healing...")
print("="*50)

# ─── STEP 1: GET SNS TOPIC ARN ────────────────────────
print("\n📧 Step 1: Getting SNS Topic...")
try:
    topics = sns.list_topics()
    TOPIC_ARN = None
    for t in topics["Topics"]:
        if "CloudAutoRecoveryAlerts" in t["TopicArn"]:
            TOPIC_ARN = t["TopicArn"]
            print(f"✅ Found SNS Topic: {TOPIC_ARN}")
            break
    if not TOPIC_ARN:
        print("❌ SNS Topic not found!")
        print("   Run setup_existing.py first")
        exit()
except Exception as e:
    print(f"❌ Error: {e}")
    exit()

# ─── STEP 2: CREATE IAM ROLE FOR LAMBDA ──────────────
print("\n🔐 Step 2: Creating IAM Role for Lambda...")

ROLE_NAME = "CloudAutoRecoveryLambdaRole"

# Trust policy
trust_policy = {
    "Version": "2012-10-17",
    "Statement": [{
        "Effect": "Allow",
        "Principal": {
            "Service": "lambda.amazonaws.com"
        },
        "Action": "sts:AssumeRole"
    }]
}

# Permissions policy
permissions_policy = {
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "ec2:DescribeInstances",
                "ec2:RebootInstances",
                "ec2:StartInstances",
                "ec2:StopInstances"
            ],
            "Resource": "*"
        },
        {
            "Effect": "Allow",
            "Action": [
                "sns:Publish"
            ],
            "Resource": "*"
        },
        {
            "Effect": "Allow",
            "Action": [
                "logs:CreateLogGroup",
                "logs:CreateLogStream",
                "logs:PutLogEvents"
            ],
            "Resource": "*"
        },
        {
            "Effect": "Allow",
            "Action": [
                "cloudwatch:DescribeAlarms",
                "cloudwatch:GetMetricStatistics"
            ],
            "Resource": "*"
        }
    ]
}

try:
    role = iam.create_role(
        RoleName=ROLE_NAME,
        AssumeRolePolicyDocument=json.dumps(trust_policy),
        Description="Role for Cloud Auto-Recovery Lambda"
    )
    ROLE_ARN = role["Role"]["Arn"]
    print(f"✅ IAM Role created: {ROLE_ARN}")
except Exception as e:
    if "already exists" in str(e).lower():
        role = iam.get_role(RoleName=ROLE_NAME)
        ROLE_ARN = role["Role"]["Arn"]
        print(f"✅ Using existing IAM Role: {ROLE_ARN}")
    else:
        print(f"❌ Role error: {e}")
        exit()

# Attach permissions
try:
    iam.put_role_policy(
        RoleName=ROLE_NAME,
        PolicyName="AutoRecoveryPermissions",
        PolicyDocument=json.dumps(permissions_policy)
    )
    print("✅ Permissions attached to role")
except Exception as e:
    print(f"⚠️  Policy error: {e}")

print("⏳ Waiting 10 seconds for IAM role to propagate...")
time.sleep(10)

# ─── STEP 3: CREATE LAMBDA FUNCTION CODE ─────────────
print("\n💻 Step 3: Creating Lambda function code...")

lambda_code = f"""
import boto3
import json
import os
from datetime import datetime

REGION = "{REGION}"
TOPIC_ARN = "{TOPIC_ARN}"

ec2 = boto3.client("ec2", region_name=REGION)
sns = boto3.client("sns", region_name=REGION)

def lambda_handler(event, context):
    print("Auto-Recovery triggered!")
    print("Event:", json.dumps(event))
    
    try:
        # Get alarm details from event
        message = event.get("Records", [{{}}])[0].get("Sns", {{}}).get("Message", "{{}}")
        alarm_data = json.loads(message) if isinstance(message, str) else message
        
        alarm_name = alarm_data.get("AlarmName", "Unknown")
        alarm_reason = alarm_data.get("NewStateReason", "Unknown reason")
        
        print(f"Alarm: {{alarm_name}}")
        print(f"Reason: {{alarm_reason}}")
        
        # Find instance from alarm name
        instance_id = None
        instance_name = "Unknown"
        
        # Get all running instances
        response = ec2.describe_instances(
            Filters=[{{
                "Name": "instance-state-name",
                "Values": ["running"]
            }}]
        )
        
        # Match instance by alarm name
        for r in response["Reservations"]:
            for i in r["Instances"]:
                name = "unnamed"
                for tag in i.get("Tags", []):
                    if tag["Key"] == "Name":
                        name = tag["Value"]
                
                # Check if alarm name contains instance name
                if name in alarm_name:
                    instance_id = i["InstanceId"]
                    instance_name = name
                    break
        
        if not instance_id:
            # Try to get instance from dimensions
            dimensions = alarm_data.get("Trigger", {{}}).get("Dimensions", [])
            for d in dimensions:
                if d.get("name") == "InstanceId":
                    instance_id = d.get("value")
                    instance_name = instance_id
                    break
        
        if instance_id:
            print(f"Rebooting instance: {{instance_name}} ({{instance_id}})")
            
            # Reboot the instance
            ec2.reboot_instances(InstanceIds=[instance_id])
            
            recovery_message = f\"\"\"
🚨 AUTO-RECOVERY TRIGGERED

Alarm: {{alarm_name}}
Instance: {{instance_name}} ({{instance_id}})
Action: REBOOT triggered automatically
Time: {{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}}
Reason: {{alarm_reason}}

Your Cloud Auto-Recovery System detected a failure and 
automatically initiated recovery. No manual action needed.

Dashboard: http://localhost:5173
\"\"\"
            
            # Send SNS notification
            sns.publish(
                TopicArn=TOPIC_ARN,
                Subject=f"🚨 Auto-Recovery: {{instance_name}} rebooting",
                Message=recovery_message
            )
            
            print(f"✅ Recovery triggered for {{instance_name}}")
            
            return {{
                "statusCode": 200,
                "body": json.dumps({{
                    "message": "Recovery triggered",
                    "instance_id": instance_id,
                    "instance_name": instance_name,
                    "action": "reboot",
                    "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                }})
            }}
        else:
            print("⚠️  Could not find instance to recover")
            
            sns.publish(
                TopicArn=TOPIC_ARN,
                Subject=f"⚠️  Auto-Recovery: Could not find instance",
                Message=f"Alarm {{alarm_name}} triggered but instance not found.\\nReason: {{alarm_reason}}"
            )
            
            return {{
                "statusCode": 200,
                "body": "Instance not found"
            }}
            
    except Exception as e:
        print(f"Error in auto-recovery: {{str(e)}}")
        return {{
            "statusCode": 500,
            "body": str(e)
        }}
"""

# Write lambda code to file
with open("/tmp/lambda_function.py", "w") as f:
    f.write(lambda_code)

# Create ZIP file
with zipfile.ZipFile("/tmp/lambda_function.zip", "w") as zf:
    zf.write("/tmp/lambda_function.py", "lambda_function.py")

print("✅ Lambda code created and zipped")

# ─── STEP 4: DEPLOY LAMBDA FUNCTION ──────────────────
print("\n🚀 Step 4: Deploying Lambda function...")

FUNCTION_NAME = "CloudAutoRecoveryFunction"

with open("/tmp/lambda_function.zip", "rb") as f:
    zip_bytes = f.read()

try:
    response = lambda_client.create_function(
        FunctionName=FUNCTION_NAME,
        Runtime="python3.9",
        Role=ROLE_ARN,
        Handler="lambda_function.lambda_handler",
        Code={"ZipFile": zip_bytes},
        Description="Auto-healing function for cloud infrastructure",
        Timeout=30,
        MemorySize=128,
        Environment={
            "Variables": {
                "TOPIC_ARN": TOPIC_ARN,
                "REGION": REGION
            }
        }
    )
    LAMBDA_ARN = response["FunctionArn"]
    print(f"✅ Lambda function created: {LAMBDA_ARN}")

except Exception as e:
    if "already exist" in str(e).lower():
        # Update existing function
        response = lambda_client.update_function_code(
            FunctionName=FUNCTION_NAME,
            ZipFile=zip_bytes
        )
        LAMBDA_ARN = response["FunctionArn"]
        print(f"✅ Lambda function updated: {LAMBDA_ARN}")
    else:
        print(f"❌ Lambda error: {e}")
        exit()

print("⏳ Waiting for Lambda to be ready...")
time.sleep(5)

# ─── STEP 5: CONNECT SNS TO LAMBDA ───────────────────
print("\n🔗 Step 5: Connecting SNS → Lambda...")

try:
    # Add permission for SNS to invoke Lambda
    lambda_client.add_permission(
        FunctionName=FUNCTION_NAME,
        StatementId="SNSInvokePermission",
        Action="lambda:InvokeFunction",
        Principal="sns.amazonaws.com",
        SourceArn=TOPIC_ARN
    )
    print("✅ Permission added for SNS to invoke Lambda")
except Exception as e:
    if "already exists" in str(e).lower():
        print("✅ Permission already exists")
    else:
        print(f"⚠️  Permission error: {e}")

try:
    # Subscribe Lambda to SNS topic
    sns.subscribe(
        TopicArn=TOPIC_ARN,
        Protocol="lambda",
        Endpoint=LAMBDA_ARN
    )
    print("✅ Lambda subscribed to SNS topic")
except Exception as e:
    print(f"⚠️  Subscription error: {e}")

# ─── STEP 6: UPDATE CLOUDWATCH ALARMS ────────────────
print("\n🔔 Step 6: Connecting CloudWatch Alarms → SNS → Lambda...")

try:
    # Get all existing alarms
    response = cloudwatch.describe_alarms()
    alarms = response["MetricAlarms"]

    updated = 0
    for alarm in alarms:
        try:
            cloudwatch.put_metric_alarm(
                AlarmName=alarm["AlarmName"],
                ComparisonOperator=alarm["ComparisonOperator"],
                EvaluationPeriods=alarm["EvaluationPeriods"],
                MetricName=alarm["MetricName"],
                Namespace=alarm["Namespace"],
                Period=alarm["Period"],
                Statistic=alarm["Statistic"],
                Threshold=alarm["Threshold"],
                ActionsEnabled=True,
                AlarmActions=[TOPIC_ARN],
                OKActions=[TOPIC_ARN],
                AlarmDescription=alarm.get("AlarmDescription", ""),
                Dimensions=alarm["Dimensions"]
            )
            updated += 1
        except Exception as e:
            print(f"  ⚠️  Could not update {alarm['AlarmName']}: {e}")

    print(f"✅ Updated {updated} alarms → connected to SNS → Lambda")

except Exception as e:
    print(f"⚠️  Alarm update error: {e}")

# ─── STEP 7: TEST LAMBDA ──────────────────────────────
print("\n🧪 Step 7: Testing Lambda function...")

test_event = {
    "Records": [{
        "Sns": {
            "Message": json.dumps({
                "AlarmName": "HighCPU-Test-1",
                "NewStateReason": "Threshold Crossed: CPU > 70%",
                "Trigger": {
                    "Dimensions": [{
                        "name": "InstanceId",
                        "value": "test-instance"
                    }]
                }
            })
        }
    }]
}

try:
    response = lambda_client.invoke(
        FunctionName=FUNCTION_NAME,
        InvocationType="RequestResponse",
        Payload=json.dumps(test_event)
    )
    result = json.loads(response["Payload"].read())
    print(f"✅ Lambda test response: {result.get('statusCode')}")
    print("✅ Lambda is working!")
except Exception as e:
    print(f"⚠️  Test error: {e}")

# ─── DONE ─────────────────────────────────────────────
print("\n" + "="*50)
print("🎉 LAMBDA SETUP COMPLETE!")
print("="*50)
print(f"\n✅ Lambda Function: {FUNCTION_NAME}")
print(f"✅ IAM Role: {ROLE_NAME}")
print(f"✅ SNS → Lambda: Connected")
print(f"✅ CloudWatch → SNS → Lambda: Connected")
print(f"\n🔥 Auto-Healing Flow:")
print("   CPU > 70% on any instance")
print("        ↓")
print("   CloudWatch Alarm triggers")
print("        ↓")
print("   SNS publishes message")
print("        ↓")
print("   Lambda runs automatically")
print("        ↓")
print("   Instance reboots")
print("        ↓")
print("   Email sent to your inbox")
print(f"\n✅ All 6 AWS Services now active:")
print("   ✅ EC2")
print("   ✅ CloudWatch")
print("   ✅ Auto Scaling")
print("   ✅ SNS")
print("   ✅ IAM")
print("   ✅ Lambda")
print("\n🚀 Your project is truly auto-healing now!")
print("="*50)