"""
Brevo (Sendinblue) CRM Integration
Syncs user signups and updates to Brevo for email marketing and CRM
"""

import os
import logging
from datetime import datetime
from typing import Optional, Dict, Any
import sib_api_v3_sdk
from sib_api_v3_sdk.rest import ApiException

logger = logging.getLogger(__name__)


class BrevoClient:
    """Client for interacting with Brevo CRM and email marketing"""

    def __init__(self):
        """Initialize Brevo API client"""
        self.api_key = os.getenv("BREVO_API_KEY")

        if not self.api_key:
            logger.warning("BREVO_API_KEY not set - Brevo integration disabled")
            self.enabled = False
            return

        # Configure API client
        configuration = sib_api_v3_sdk.Configuration()
        configuration.api_key['api-key'] = self.api_key

        # Initialize API instances
        self.contacts_api = sib_api_v3_sdk.ContactsApi(sib_api_v3_sdk.ApiClient(configuration))
        self.lists_api = sib_api_v3_sdk.ContactsApi(sib_api_v3_sdk.ApiClient(configuration))
        self.transactional_api = sib_api_v3_sdk.TransactionalEmailsApi(sib_api_v3_sdk.ApiClient(configuration))

        self.enabled = True
        logger.info("Brevo CRM client initialized successfully")

    def create_or_update_contact(
        self,
        email: str,
        attributes: Dict[str, Any],
        list_ids: Optional[list] = None
    ) -> bool:
        """
        Create or update a contact in Brevo

        Args:
            email: Contact email address
            attributes: Contact attributes (firstname, lastname, etc.)
            list_ids: List IDs to add contact to (optional)

        Returns:
            bool: True if successful, False otherwise
        """
        if not self.enabled:
            logger.debug("Brevo integration disabled, skipping contact sync")
            return False

        try:
            # Create contact object
            create_contact = sib_api_v3_sdk.CreateContact(
                email=email,
                attributes=attributes,
                list_ids=list_ids or [],
                update_enabled=True  # Update if contact already exists
            )

            # Create or update contact
            api_response = self.contacts_api.create_contact(create_contact)
            logger.info(f"Successfully synced contact to Brevo: {email}")
            return True

        except ApiException as e:
            # Check if contact already exists (duplicate error)
            if "duplicate_parameter" in str(e):
                logger.info(f"Contact already exists in Brevo, updating: {email}")
                return self.update_contact(email, attributes)
            else:
                logger.error(f"Error creating Brevo contact: {e}")
                return False
        except Exception as e:
            logger.error(f"Unexpected error syncing to Brevo: {e}")
            return False

    def update_contact(self, email: str, attributes: Dict[str, Any]) -> bool:
        """
        Update an existing contact in Brevo

        Args:
            email: Contact email address
            attributes: Attributes to update

        Returns:
            bool: True if successful, False otherwise
        """
        if not self.enabled:
            return False

        try:
            update_contact = sib_api_v3_sdk.UpdateContact(
                attributes=attributes
            )

            self.contacts_api.update_contact(email, update_contact)
            logger.info(f"Successfully updated Brevo contact: {email}")
            return True

        except ApiException as e:
            logger.error(f"Error updating Brevo contact: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error updating Brevo contact: {e}")
            return False

    def add_contact_to_list(self, email: str, list_id: int) -> bool:
        """
        Add a contact to a specific list

        Args:
            email: Contact email
            list_id: Brevo list ID

        Returns:
            bool: True if successful
        """
        if not self.enabled:
            return False

        try:
            contact_emails = sib_api_v3_sdk.AddContactToList(emails=[email])
            self.lists_api.add_contact_to_list(list_id, contact_emails)
            logger.info(f"Added contact {email} to list {list_id}")
            return True
        except ApiException as e:
            logger.error(f"Error adding contact to list: {e}")
            return False

    def sync_new_signup(
        self,
        email: str,
        full_name: str,
        username: str,
        trial_start: str,
        trial_days: int = 7
    ) -> bool:
        """
        Sync a new user signup to Brevo

        Args:
            email: User email
            full_name: User's full name
            username: Username
            trial_start: Trial start datetime (ISO format)
            trial_days: Trial duration in days

        Returns:
            bool: True if successful
        """
        # Split name into first and last
        name_parts = full_name.split(maxsplit=1)
        firstname = name_parts[0] if name_parts else ""
        lastname = name_parts[1] if len(name_parts) > 1 else ""

        # Prepare contact attributes
        attributes = {
            "FIRSTNAME": firstname,
            "LASTNAME": lastname,
            "USERNAME": username,
            "TRIAL_START": trial_start,
            "TRIAL_DAYS": trial_days,
            "SIGNUP_DATE": datetime.now().isoformat(),
            "ACCOUNT_STATUS": "trial",
            "SUBSCRIPTION_TIER": "free_trial",
            "SMS": "",  # Optional: add phone if collected
        }

        # Optional: Add to trial users list (create this list in Brevo first)
        # Get the list ID from environment variable
        trial_list_id = os.getenv("BREVO_TRIAL_LIST_ID")
        list_ids = [int(trial_list_id)] if trial_list_id else []

        return self.create_or_update_contact(email, attributes, list_ids)

    def sync_subscription_upgrade(
        self,
        email: str,
        subscription_tier: str,
        stripe_subscription_id: str
    ) -> bool:
        """
        Update contact when they upgrade to paid subscription

        Args:
            email: User email
            subscription_tier: Tier name (pro, elite, etc.)
            stripe_subscription_id: Stripe subscription ID

        Returns:
            bool: True if successful
        """
        attributes = {
            "ACCOUNT_STATUS": "active",
            "SUBSCRIPTION_TIER": subscription_tier.upper(),
            "STRIPE_SUBSCRIPTION_ID": stripe_subscription_id,
            "UPGRADE_DATE": datetime.now().isoformat()
        }

        # Move to paid users list
        paid_list_id = os.getenv("BREVO_PAID_LIST_ID")
        if paid_list_id:
            self.add_contact_to_list(email, int(paid_list_id))

        return self.update_contact(email, attributes)

    def sync_trial_expired(self, email: str) -> bool:
        """
        Update contact when trial expires

        Args:
            email: User email

        Returns:
            bool: True if successful
        """
        attributes = {
            "ACCOUNT_STATUS": "trial_expired",
            "TRIAL_EXPIRED_DATE": datetime.now().isoformat()
        }

        # Move to trial expired list
        expired_list_id = os.getenv("BREVO_TRIAL_EXPIRED_LIST_ID")
        if expired_list_id:
            self.add_contact_to_list(email, int(expired_list_id))

        return self.update_contact(email, attributes)

    def sync_cancellation(self, email: str) -> bool:
        """
        Update contact when they cancel subscription

        Args:
            email: User email

        Returns:
            bool: True if successful
        """
        attributes = {
            "ACCOUNT_STATUS": "cancelled",
            "CANCELLATION_DATE": datetime.now().isoformat()
        }

        # Move to churned users list
        churned_list_id = os.getenv("BREVO_CHURNED_LIST_ID")
        if churned_list_id:
            self.add_contact_to_list(email, int(churned_list_id))

        return self.update_contact(email, attributes)

    def send_welcome_email_with_extension(
        self,
        email: str,
        full_name: str
    ) -> bool:
        """
        Send welcome email with download links for Chrome extension

        Args:
            email: Recipient email
            full_name: User's full name

        Returns:
            bool: True if successful
        """
        if not self.enabled:
            return False

        try:
            import base64

            # Split name for personalization
            name_parts = full_name.split(maxsplit=1)
            firstname = name_parts[0] if name_parts else "there"

            # Download URLs for extension and guide
            # Use environment variable for website URL (defaults to production)
            website_url = os.getenv("WEBSITE_URL", "https://max-ev-sports.com")
            extension_download_url = f"{website_url}/downloads/MAX-EV_Sports_Extension.zip"
            guide_download_url = f"{website_url}/downloads/Installation_Guide.pdf"
            logo_url = f"{website_url}/assets/12225.png"

            # Email HTML content
            html_content = f"""
            <div style="text-align: center; margin-bottom: 30px;">
                <img src="{logo_url}" alt="Max EV Sports" style="width: 200px; height: auto; max-width: 100%;" />
            </div>

            <h2>Hi {firstname},</h2>

            <p>Welcome to MAX-EV Sports! 🏀⚾🏈</p>

            <p>You now have access to our professional sports betting analytics platform with advanced ML predictions and real-time betting opportunities.</p>

            <h3>What's Included:</h3>
            <ul>
                <li>🏀 <strong>Web Platform</strong> - Access live odds, projections, and analytics at <a href="https://www.max-ev-sports.com/">https://www.max-ev-sports.com/</a></li>
                <li>🏈 <strong>ML Predictions</strong> - Advanced machine learning models for NBA, NHL, NFL, and more</li>
                <li>⚾ <strong>Real-Time Data</strong> - Updated every 10 seconds with the latest opportunities</li>
                <li>🏒 <strong>Professional Tools</strong> - Built by professional sports bettors for serious players</li>
            </ul>

            <hr>

            <h3>Get Started in 2 Steps:</h3>

            <h4>1. Access Your Account</h4>
            <ul>
                <li><strong>Website:</strong> <a href="https://www.max-ev-sports.com/">https://www.max-ev-sports.com/</a></li>
                <li><strong>Email:</strong> {email}</li>
            </ul>

            <h4>2. Start Finding Opportunities</h4>
            <ul>
                <li>Browse today's predictions and edges on the dashboard</li>
                <li>Check out player props with our advanced ML models</li>
                <li>Explore betting strategies and performance analytics</li>
                <li>Track your bets and analyze your performance</li>
            </ul>

            <hr>

            <h3>What You'll Find:</h3>
            <ul>
                <li>🏀 <strong>Arbitrage Opportunities</strong> - Risk-free profits (2-5% returns)</li>
                <li>🏈 <strong>Middle Opportunities</strong> - Bet both sides with a gap (potential to win both)</li>
                <li>⚾ <strong>Steam Moves</strong> - Sharp money detection (follow the pros)</li>
                <li>🏒 <strong>Goalie Pull Alerts</strong> - NHL empty net betting (8-12% edge)</li>
            </ul>

            <hr>

            <h3>Pro Tips for Success:</h3>
            <ol>
                <li><strong>Have Multiple Books</strong> - At least 3-5 accounts (DraftKings, FanDuel, BetMGM, Caesars, BetRivers)</li>
                <li><strong>Start Small</strong> - Test with smaller amounts until you're comfortable with the platform</li>
                <li><strong>Review Model Performance</strong> - Check our model performance page to see historical accuracy</li>
                <li><strong>Use the Filters</strong> - Filter predictions by sport, confidence level, and edge percentage</li>
                <li><strong>Track Your Bets</strong> - Use our bet tracking feature to monitor your performance</li>
            </ol>

            <hr>

            <h3>Need Help?</h3>
            <p>Reply to this email or contact: <a href="mailto:support@max-ev-sports.com">support@max-ev-sports.com</a></p>

            <p><strong>Let's start finding profitable opportunities together!</strong></p>

            <p>The MAX-EV Sports Team</p>

            <hr>

            <p><em>P.S. Our platform is constantly updated with new features and improvements. Stay tuned for exciting updates!</em></p>
            """

            # Create email object (without attachments - users download from website)
            sender_email = os.getenv("BREVO_SENDER_EMAIL", "noreply@max-ev-sports.com")
            send_smtp_email = sib_api_v3_sdk.SendSmtpEmail(
                to=[{"email": email, "name": full_name}],
                sender={"email": sender_email, "name": "MAX-EV Sports"},
                subject="Welcome to MAX-EV Sports - Your Account is Ready!",
                html_content=html_content
                # Note: No 'attachment' parameter - users download from website instead
            )

            # Send email
            api_response = self.transactional_api.send_transac_email(send_smtp_email)
            logger.info(f"Successfully sent welcome email with extension to: {email}")
            return True

        except ApiException as e:
            logger.error(f"Error sending welcome email via Brevo: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error sending welcome email: {e}")
            return False

    def send_admin_notification(
        self,
        notification_type: str,
        subject: str,
        details: Dict[str, Any]
    ) -> bool:
        """
        Send notification email to admin

        Args:
            notification_type: Type of notification (signup, payment, etc.)
            subject: Email subject
            details: Dictionary of notification details

        Returns:
            bool: True if successful
        """
        if not self.enabled:
            return False

        try:
            # Get admin email from environment
            admin_email = os.getenv("ADMIN_EMAIL", "gte.apw@gmail.com")
            website_url = os.getenv("WEBSITE_URL", "https://max-ev-sports.com")
            logo_url = f"{website_url}/assets/12225.png"

            # Build HTML content based on notification type
            if notification_type == "signup":
                html_content = f"""
                <div style="text-align: center; margin-bottom: 30px;">
                    <img src="{logo_url}" alt="Max EV Sports" style="width: 150px; height: auto; max-width: 100%;" />
                </div>

                <h2>🏀 New User Signup</h2>
                <p>A new user just signed up for MAX-EV Sports!</p>

                <table style="border-collapse: collapse; width: 100%; max-width: 500px;">
                    <tr style="background-color: #f8f9fa;">
                        <td style="padding: 10px; border: 1px solid #dee2e6; font-weight: bold;">Username</td>
                        <td style="padding: 10px; border: 1px solid #dee2e6;">{details.get('username', 'N/A')}</td>
                    </tr>
                    <tr>
                        <td style="padding: 10px; border: 1px solid #dee2e6; font-weight: bold;">Full Name</td>
                        <td style="padding: 10px; border: 1px solid #dee2e6;">{details.get('full_name', 'N/A')}</td>
                    </tr>
                    <tr style="background-color: #f8f9fa;">
                        <td style="padding: 10px; border: 1px solid #dee2e6; font-weight: bold;">Email</td>
                        <td style="padding: 10px; border: 1px solid #dee2e6;">{details.get('email', 'N/A')}</td>
                    </tr>
                    <tr>
                        <td style="padding: 10px; border: 1px solid #dee2e6; font-weight: bold;">Timestamp</td>
                        <td style="padding: 10px; border: 1px solid #dee2e6;">{details.get('timestamp', 'N/A')}</td>
                    </tr>
                </table>

                <p style="margin-top: 20px;">
                    <a href="https://www.max-ev-sports.com/admin" style="display: inline-block; background-color: #4CAF50; color: white; padding: 12px 24px; text-decoration: none; border-radius: 5px;">View in Admin Panel</a>
                </p>
                """

            elif notification_type == "payment":
                html_content = f"""
                <div style="text-align: center; margin-bottom: 30px;">
                    <img src="{logo_url}" alt="Max EV Sports" style="width: 150px; height: auto; max-width: 100%;" />
                </div>

                <h2>🏈 New Payment Received</h2>
                <p>A user just completed a payment!</p>

                <table style="border-collapse: collapse; width: 100%; max-width: 500px;">
                    <tr style="background-color: #f8f9fa;">
                        <td style="padding: 10px; border: 1px solid #dee2e6; font-weight: bold;">Full Name</td>
                        <td style="padding: 10px; border: 1px solid #dee2e6;">{details.get('full_name', 'N/A')}</td>
                    </tr>
                    <tr>
                        <td style="padding: 10px; border: 1px solid #dee2e6; font-weight: bold;">Email</td>
                        <td style="padding: 10px; border: 1px solid #dee2e6;">{details.get('email', 'N/A')}</td>
                    </tr>
                    <tr style="background-color: #f8f9fa;">
                        <td style="padding: 10px; border: 1px solid #dee2e6; font-weight: bold;">Tier</td>
                        <td style="padding: 10px; border: 1px solid #dee2e6;"><strong>{details.get('tier', 'N/A')}</strong></td>
                    </tr>
                    <tr>
                        <td style="padding: 10px; border: 1px solid #dee2e6; font-weight: bold;">Amount</td>
                        <td style="padding: 10px; border: 1px solid #dee2e6;"><strong style="color: #28a745; font-size: 18px;">{details.get('amount', 'N/A')}</strong></td>
                    </tr>
                    <tr style="background-color: #f8f9fa;">
                        <td style="padding: 10px; border: 1px solid #dee2e6; font-weight: bold;">Timestamp</td>
                        <td style="padding: 10px; border: 1px solid #dee2e6;">{details.get('timestamp', 'N/A')}</td>
                    </tr>
                </table>

                <p style="margin-top: 20px;">
                    <a href="https://dashboard.stripe.com/payments" style="display: inline-block; background-color: #6772e5; color: white; padding: 12px 24px; text-decoration: none; border-radius: 5px;">View in Stripe</a>
                </p>
                """

            elif notification_type == "waitlist":
                html_content = f"""
                <div style="text-align: center; margin-bottom: 30px;">
                    <img src="{logo_url}" alt="Max EV Sports" style="width: 150px; height: auto; max-width: 100%;" />
                </div>

                <h2>⚾ New Waitlist Signup</h2>
                <p>Someone just joined the pricing page waitlist!</p>

                <table style="border-collapse: collapse; width: 100%; max-width: 500px;">
                    <tr style="background-color: #f8f9fa;">
                        <td style="padding: 10px; border: 1px solid #dee2e6; font-weight: bold;">Email</td>
                        <td style="padding: 10px; border: 1px solid #dee2e6;">{details.get('email', 'N/A')}</td>
                    </tr>
                    <tr>
                        <td style="padding: 10px; border: 1px solid #dee2e6; font-weight: bold;">Tier</td>
                        <td style="padding: 10px; border: 1px solid #dee2e6;"><strong>{details.get('tier', 'N/A')}</strong></td>
                    </tr>
                    <tr style="background-color: #f8f9fa;">
                        <td style="padding: 10px; border: 1px solid #dee2e6; font-weight: bold;">Price</td>
                        <td style="padding: 10px; border: 1px solid #dee2e6;"><strong style="color: #2196F3; font-size: 18px;">{details.get('price', 'N/A')}</strong></td>
                    </tr>
                    <tr>
                        <td style="padding: 10px; border: 1px solid #dee2e6; font-weight: bold;">Timestamp</td>
                        <td style="padding: 10px; border: 1px solid #dee2e6;">{details.get('timestamp', 'N/A')}</td>
                    </tr>
                </table>

                <p style="margin-top: 20px;">
                    <a href="https://app.brevo.com/contact/list-listing/11" style="display: inline-block; background-color: #0B996E; color: white; padding: 12px 24px; text-decoration: none; border-radius: 5px;">View in Brevo</a>
                </p>
                """
            else:
                html_content = f"<p>{details}</p>"

            # Create email object
            sender_email = os.getenv("BREVO_SENDER_EMAIL", "noreply@max-ev-sports.com")
            send_smtp_email = sib_api_v3_sdk.SendSmtpEmail(
                to=[{"email": admin_email}],
                sender={"email": sender_email, "name": "MAX-EV Sports Notifications"},
                subject=subject,
                html_content=html_content
            )

            # Send email
            api_response = self.transactional_api.send_transac_email(send_smtp_email)
            logger.info(f"Successfully sent admin notification: {notification_type}")
            return True

        except ApiException as e:
            logger.error(f"Error sending admin notification via Brevo: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error sending admin notification: {e}")
            return False


# Load environment variables before initializing client
from dotenv import load_dotenv
load_dotenv()

# Global Brevo client instance
brevo_client = BrevoClient()


# Convenience functions
def sync_signup_to_brevo(email: str, full_name: str, username: str, trial_start: str, trial_days: int = 7):
    """Sync new user signup to Brevo CRM"""
    return brevo_client.sync_new_signup(email, full_name, username, trial_start, trial_days)


def sync_upgrade_to_brevo(email: str, subscription_tier: str, stripe_subscription_id: str):
    """Sync subscription upgrade to Brevo CRM"""
    return brevo_client.sync_subscription_upgrade(email, subscription_tier, stripe_subscription_id)


def sync_trial_expired_to_brevo(email: str):
    """Sync trial expiration to Brevo CRM"""
    return brevo_client.sync_trial_expired(email)


def sync_cancellation_to_brevo(email: str):
    """Sync subscription cancellation to Brevo CRM"""
    return brevo_client.sync_cancellation(email)


def send_welcome_email(email: str, full_name: str):
    """Send welcome email with Chrome extension download links"""
    return brevo_client.send_welcome_email_with_extension(email, full_name)


def send_admin_signup_notification(email: str, full_name: str, username: str):
    """Send admin notification for new user signup"""
    return brevo_client.send_admin_notification(
        notification_type="signup",
        subject="🎉 New User Signup - MAX-EV Sports",
        details={
            "email": email,
            "full_name": full_name,
            "username": username,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
    )


def send_admin_payment_notification(email: str, full_name: str, tier: str, amount: float):
    """Send admin notification for successful payment"""
    return brevo_client.send_admin_notification(
        notification_type="payment",
        subject="💰 New Payment Received - MAX-EV Sports",
        details={
            "email": email,
            "full_name": full_name,
            "tier": tier,
            "amount": f"${amount:.2f}",
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
    )


def send_admin_waitlist_notification(email: str, tier: str, price: float):
    """Send admin notification for pricing page waitlist signup"""
    return brevo_client.send_admin_notification(
        notification_type="waitlist",
        subject="📋 New Waitlist Signup - MAX-EV Sports",
        details={
            "email": email,
            "tier": tier,
            "price": f"${price:.2f}",
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
    )
