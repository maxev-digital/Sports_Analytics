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
