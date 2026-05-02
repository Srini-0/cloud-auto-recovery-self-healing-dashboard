"""
fix_sns_email.py — Re-subscribes your email to the SNS topic.
Usage: cd Backend && python fix_sns_email.py
"""
import boto3

REGION = "us-west-1"
TOPIC_ARN = "arn:aws:sns:us-west-1:432629722871:CloudAutoRecoveryAlerts"
EMAIL = "sakthiseenu2004@gmail.com"

sns = boto3.client("sns", region_name=REGION)

print(f"\n📧 Re-subscribing {EMAIL} to SNS topic...")

try:
    response = sns.subscribe(
        TopicArn=TOPIC_ARN,
        Protocol="email",
        Endpoint=EMAIL,
        ReturnSubscriptionArn=True
    )
    print(f"✅ Subscription request sent!")
    print(f"   ARN: {response.get('SubscriptionArn')}")
    print(f"\n⚠️  ACTION REQUIRED:")
    print(f"   1. Open Gmail for {EMAIL}")
    print(f"   2. Look for email from 'AWS Notifications'")
    print(f"   3. Click 'Confirm subscription' link in that email")
    print(f"   4. Once confirmed, run: python diagnose_sns.py")
    print(f"      to send a test email and verify it works")
except Exception as e:
    print(f"❌ Error: {e}")
