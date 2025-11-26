"""
Upload Day 10 Trial Reminder Email Template to Brevo
This script creates the email template in Brevo via API
"""

import os
import sys
from pathlib import Path
import sib_api_v3_sdk
from sib_api_v3_sdk.rest import ApiException
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def upload_email_template():
    """Upload the Day 10 trial reminder email template to Brevo"""

    # Get Brevo API key
    api_key = os.getenv("BREVO_API_KEY")
    if not api_key:
        print("❌ ERROR: BREVO_API_KEY not found in environment variables")
        print("Please add BREVO_API_KEY to your .env file")
        return False

    # Configure API client
    configuration = sib_api_v3_sdk.Configuration()
    configuration.api_key['api-key'] = api_key

    # Create SMTP Templates API instance
    api_instance = sib_api_v3_sdk.SMTPApi(sib_api_v3_sdk.ApiClient(configuration))

    # Read the HTML template
    template_path = Path(__file__).parent / "brevo_day10_trial_reminder.html"

    if not template_path.exists():
        print(f"❌ ERROR: Template file not found at {template_path}")
        return False

    with open(template_path, 'r', encoding='utf-8') as f:
        html_content = f.read()

    print("📧 Creating email template in Brevo...")
    print(f"Template file: {template_path}")
    print(f"HTML content length: {len(html_content)} characters")

    # Create the template
    smtp_template = sib_api_v3_sdk.CreateSmtpTemplate(
        sender=sib_api_v3_sdk.CreateSmtpTemplateSender(
            name="Max EV Sports",
            email="noreply@max-ev-sports.com"  # Update with your verified sender email
        ),
        template_name="Day 10 Trial Reminder - Choose Your Plan",
        html_content=html_content,
        subject="⏰ Your Trial Ends Soon - Choose Your Plan",
        is_active=True,
        tag="trial-reminder"
    )

    try:
        # Create template
        api_response = api_instance.create_smtp_template(smtp_template)
        template_id = api_response.id

        print("\n" + "="*80)
        print("✅ SUCCESS! Email template uploaded to Brevo")
        print("="*80)
        print(f"\nTemplate ID: {template_id}")
        print(f"Template Name: Day 10 Trial Reminder - Choose Your Plan")
        print(f"Subject: ⏰ Your Trial Ends Soon - Choose Your Plan")
        print(f"\n🔗 View in Brevo: https://app.brevo.com/camp/template/{template_id}")
        print("\n" + "="*80)
        print("\n📋 NEXT STEPS:")
        print("="*80)
        print("\n1. Go to Brevo → Automation → Create new automation")
        print("2. Name: 'Trial Day 10 Reminder'")
        print("3. Entry trigger: Contact attribute 'TRIAL_START' is set")
        print("4. Add wait step: 10 days")
        print("5. Add condition: SUBSCRIPTION_TIER = 'trialing' OR 'free'")
        print(f"6. Add send email action: Select template ID {template_id}")
        print("7. Activate the automation")
        print("\n" + "="*80)

        return True

    except ApiException as e:
        print(f"\n❌ ERROR: Failed to create template in Brevo")
        print(f"Status code: {e.status}")
        print(f"Reason: {e.reason}")
        print(f"Body: {e.body}")

        # Check for common errors
        if e.status == 400:
            print("\n💡 TIP: Make sure 'noreply@max-ev-sports.com' is a verified sender in Brevo")
            print("Or update the sender email in this script to match a verified sender.")
        elif e.status == 401:
            print("\n💡 TIP: Check that your BREVO_API_KEY is correct and active")

        return False
    except Exception as e:
        print(f"\n❌ UNEXPECTED ERROR: {type(e).__name__}: {e}")
        return False


def create_automation_instructions():
    """Print instructions for creating the automation in Brevo web UI"""

    print("\n" + "="*80)
    print("🤖 AUTOMATION SETUP INSTRUCTIONS")
    print("="*80)

    instructions = """
Since Brevo automations require visual workflow setup, please create the
automation manually in the Brevo web interface:

📍 Step-by-Step:

1. Login to Brevo: https://app.brevo.com/
2. Navigate to: Automation → Create an automation
3. Select: "Build from scratch"
4. Name: "Trial Day 10 Reminder"

5. ENTRY POINT:
   - Trigger: "Contact attribute updated"
   - Attribute: TRIAL_START
   - Condition: "exists" (triggers when trial_start is set)

6. ADD WAIT STEP:
   - Click "+" button
   - Select "Wait"
   - Duration: 10 days
   - Description: "Wait 10 days after trial start"

7. ADD CONDITION (Optional but recommended):
   - Click "+" button
   - Select "Condition"
   - Attribute: SUBSCRIPTION_TIER
   - Condition: "equals" → "trialing" OR "free"
   - This prevents sending to users who already subscribed

8. ADD EMAIL ACTION:
   - Click "+" button
   - Select "Send an email"
   - Template: "Day 10 Trial Reminder - Choose Your Plan"
   - Sender: Your verified sender

9. REVIEW & ACTIVATE:
   - Review the workflow
   - Click "Activate"

✅ Your automation will now send automatically 10 days after each signup!

Expected Flow:
  Contact created with TRIAL_START
         ↓
    Wait 10 days
         ↓
  Check if still on trial (optional condition)
         ↓
  Send "Day 10 Trial Reminder" email
         ↓
  User clicks tier button → Stripe checkout → Conversion!
"""

    print(instructions)
    print("="*80)


if __name__ == "__main__":
    print("\n" + "="*80)
    print("📧 BREVO DAY 10 TRIAL REMINDER EMAIL SETUP")
    print("="*80 + "\n")

    success = upload_email_template()

    if success:
        create_automation_instructions()
        print("\n✅ Template upload complete!")
        print("📋 Follow the automation instructions above to complete setup\n")
        sys.exit(0)
    else:
        print("\n❌ Template upload failed. Please check the errors above.\n")
        sys.exit(1)
