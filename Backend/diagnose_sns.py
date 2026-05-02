"""
diagnose_sns.py — Run this to find exactly why emails aren't arriving.
Usage: cd Backend && python diagnose_sns.py
"""
import boto3
import json

REGION = "us-west-1"

sns = boto3.client("sns", region_name=REGION)
iam = boto3.client("iam")
sts = boto3.client("sts")

print("\n" + "=" * 60)
print("  SNS EMAIL DIAGNOSTIC")
print("=" * 60)

# ─── STEP 1: AWS Identity ─────────────────────────────
print("\n[1] Checking AWS credentials...")
try:
    identity = sts.get_caller_identity()
    print(f"  ✅ Account: {identity['Account']}")
    print(f"  ✅ ARN:     {identity['Arn']}")
except Exception as e:
    print(f"  ❌ AWS credentials not configured: {e}")
    print("     Run: aws configure")
    exit(1)

# ─── STEP 2: SNS Topic ───────────────────────────────
print("\n[2] Checking SNS topic...")
topic_arn = None
try:
    topics = sns.list_topics().get("Topics", [])
    for t in topics:
        if "CloudAutoRecoveryAlerts" in t["TopicArn"]:
            topic_arn = t["TopicArn"]
            break
    if topic_arn:
        print(f"  ✅ Topic found: {topic_arn}")
    else:
        print("  ❌ Topic 'CloudAutoRecoveryAlerts' NOT found")
        print("     Creating it now...")
        topic_arn = sns.create_topic(Name="CloudAutoRecoveryAlerts")["TopicArn"]
        print(f"  ✅ Topic created: {topic_arn}")
except Exception as e:
    print(f"  ❌ SNS error: {e}")
    exit(1)

# ─── STEP 3: Subscriptions ───────────────────────────
print("\n[3] Checking subscriptions...")
try:
    subs = sns.list_subscriptions_by_topic(TopicArn=topic_arn).get("Subscriptions", [])
    if not subs:
        print("  ❌ NO subscriptions found — nobody will receive emails!")
        email = input("\n  Enter your email to subscribe now: ").strip()
        if email and "@" in email:
            sns.subscribe(TopicArn=topic_arn, Protocol="email", Endpoint=email)
            print(f"  ✅ Subscription request sent to {email}")
            print("  ⚠️  CHECK YOUR INBOX and click the confirmation link!")
        else:
            print("  ⚠️  Skipped. Add a subscription manually in AWS Console.")
    else:
        for s in subs:
            status = s["SubscriptionArn"]
            endpoint = s["Endpoint"]
            protocol = s["Protocol"]
            if status == "PendingConfirmation":
                print(f"  ⏳ PENDING: {endpoint} ({protocol}) — not confirmed yet!")
                print(f"     Check inbox for '{endpoint}' and click the AWS confirmation link")
            elif status == "Deleted":
                print(f"  ❌ DELETED: {endpoint} — subscription was deleted")
            else:
                print(f"  ✅ CONFIRMED: {endpoint} ({protocol})")
except Exception as e:
    print(f"  ❌ Subscription check error: {e}")

# ─── STEP 4: Send test email ─────────────────────────
print("\n[4] Sending test email...")
try:
    confirmed_subs = [
        s for s in sns.list_subscriptions_by_topic(TopicArn=topic_arn).get("Subscriptions", [])
        if s["SubscriptionArn"] not in ("PendingConfirmation", "Deleted")
    ]
    if not confirmed_subs:
        print("  ⚠️  Skipping test — no confirmed subscriptions")
        print("     Confirm your subscription first, then re-run this script")
    else:
        response = sns.publish(
            TopicArn=topic_arn,
            Subject="✅ Test: Auto-Recovery Dashboard Alert",
            Message=(
                "This is a test alert from your Auto-Recovery Dashboard.\n\n"
                "If you received this, SNS email alerts are working correctly.\n\n"
                "You will automatically receive alerts when:\n"
                "  - CPU > 70% on any instance (reboot triggered)\n"
                "  - Instance stops or terminates\n"
                "  - Instance recovers\n"
            )
        )
        print(f"  ✅ Test email published! MessageId: {response['MessageId']}")
        print(f"  📬 Check inbox for: {[s['Endpoint'] for s in confirmed_subs]}")
except Exception as e:
    print(f"  ❌ Publish failed: {e}")

# ─── STEP 5: IAM permissions check ───────────────────
print("\n[5] Checking SNS publish permissions...")
try:
    # Try a dry-run by checking policy (best effort)
    policy = sns.get_topic_attributes(TopicArn=topic_arn).get("Attributes", {})
    print(f"  ✅ Topic accessible — DisplayName: '{policy.get('DisplayName', '(none)')}'")
    print(f"  ✅ Subscriptions confirmed: {policy.get('SubscriptionsConfirmed', '0')}")
    print(f"  ⏳ Subscriptions pending:   {policy.get('SubscriptionsPending', '0')}")
except Exception as e:
    print(f"  ⚠️  Could not read topic attributes: {e}")

print("\n" + "=" * 60)
print("  DIAGNOSIS COMPLETE")
print("=" * 60)
print("\nNext steps:")
print("  1. If subscription is PENDING → confirm it from your email inbox")
print("  2. If no subscription → re-run this script and enter your email")
print("  3. If test email sent → restart Flask: python app.py")
print("  4. Trigger a CPU stress test to verify live alerts work")
print()
