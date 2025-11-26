"""
Upload Day 10 Trial Reminder Email Template to Brevo (Simple version without emojis)
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
        print("ERROR: BREVO_API_KEY not found in environment variables")
        print("Please add BREVO_API_KEY to your .env file")
        return False

    # Configure API client
    configuration = sib_api_v3_sdk.Configuration()
    configuration.api_key['api-key'] = api_key

    # Create Transactional Emails API instance
    api_instance = sib_api_v3_sdk.TransactionalEmailsApi(sib_api_v3_sdk.ApiClient(configuration))

    # Read the HTML template
    template_path = Path(__file__).parent / "brevo_day10_trial_reminder.html"

    if not template_path.exists():
        print(f"ERROR: Template file not found at {template_path}")
        return False

    with open(template_path, 'r', encoding='utf-8') as f:
        html_content = f.read()

    print("Creating email template in Brevo...")
    print(f"Template file: {template_path}")
    print(f"HTML content length: {len(html_content)} characters")

    # Get sender email from environment variable
    sender_email = os.getenv("BREVO_SENDER_EMAIL", "willaustin@max-ev-sports.com")

    # Create the template
    smtp_template = sib_api_v3_sdk.CreateSmtpTemplate(
        sender=sib_api_v3_sdk.CreateSmtpTemplateSender(
            name="Max EV Sports",
            email=sender_email
        ),
        template_name="Day 10 Trial Reminder - Choose Your Plan",
        html_content=html_content,
        subject="Your Trial Ends Soon - Choose Your Plan",
        is_active=True,
        tag="trial-reminder"
    )

    try:
        # Create template
        api_response = api_instance.create_smtp_template(smtp_template)
        template_id = api_response.id

        print("\n" + "="*80)
        print("SUCCESS! Email template uploaded to Brevo")
        print("="*80)
        print(f"\nTemplate ID: {template_id}")
        print(f"Template Name: Day 10 Trial Reminder - Choose Your Plan")
        print(f"Subject: Your Trial Ends Soon - Choose Your Plan")
        print(f"\nView in Brevo: https://app.brevo.com/camp/template/{template_id}")
        print("\n" + "="*80)
        print("\nNEXT STEPS:")
        print("="*80)
        print("\n1. Go to Brevo > Automation > Create new automation")
        print("2. Name: 'Trial Day 10 Reminder'")
        print("3. Entry trigger: Contact attribute 'TRIAL_START' is set")
        print("4. Add wait step: 10 days")
        print("5. Add condition: SUBSCRIPTION_TIER = 'trialing' OR 'free'")
        print(f"6. Add send email action: Select template ID {template_id}")
        print("7. Activate the automation")
        print("\n" + "="*80)

        return True

    except ApiException as e:
        print(f"\nERROR: Failed to create template in Brevo")
        print(f"Status code: {e.status}")
        print(f"Reason: {e.reason}")
        print(f"Body: {e.body}")

        # Check for common errors
        if e.status == 400:
            print("\nTIP: Make sure 'noreply@max-ev-sports.com' is a verified sender in Brevo")
            print("Or update the sender email in this script to match a verified sender.")
        elif e.status == 401:
            print("\nTIP: Check that your BREVO_API_KEY is correct and active")

        return False
    except Exception as e:
        print(f"\nUNEXPECTED ERROR: {type(e).__name__}: {e}")
        return False


if __name__ == "__main__":
    print("\n" + "="*80)
    print("BREVO DAY 10 TRIAL REMINDER EMAIL SETUP")
    print("="*80 + "\n")

    success = upload_email_template()

    if success:
        print("\nTemplate upload complete!")
        print("Follow the automation instructions above to complete setup\n")
        sys.exit(0)
    else:
        print("\nTemplate upload failed. Please check the errors above.\n")
        sys.exit(1)
