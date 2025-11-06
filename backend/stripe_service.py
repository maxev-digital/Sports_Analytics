"""
Stripe Payment Processing Service
Handles all Stripe-related operations for subscription management
"""

import os
import stripe
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from dotenv import load_dotenv
from pathlib import Path

# Load environment variables from backend/.env
backend_dir = Path(__file__).parent
env_path = backend_dir / '.env'
load_dotenv(dotenv_path=env_path)

# Initialize Stripe with secret key
stripe.api_key = os.getenv("STRIPE_SECRET_KEY")
if not stripe.api_key:
    print("WARNING: STRIPE_SECRET_KEY not found in environment variables!")
else:
    print(f"Stripe initialized with API key: {stripe.api_key[:20]}...")

# Price IDs from environment
STRIPE_BETA_PRICE_ID = "price_1SQEZcR1TzxiBDhGeZgpoWVN"  # Beta Launch $9.99/mo
STRIPE_STARTER_PRICE_ID = os.getenv("STRIPE_STARTER_PRICE_ID")
STRIPE_SEMIPRO_PRICE_ID = os.getenv("STRIPE_SEMIPRO_PRICE_ID")
STRIPE_PROFESSIONAL_PRICE_ID = os.getenv("STRIPE_PROFESSIONAL_PRICE_ID")
STRIPE_ELITE_PRICE_ID = os.getenv("STRIPE_ELITE_PRICE_ID")
STRIPE_ELITEPRO_PRICE_ID = os.getenv("STRIPE_ELITEPRO_PRICE_ID")

# Beta Launch Promo Code (50% OFF FOR LIFE)
STRIPE_BETA_PROMO_CODE = os.getenv("STRIPE_BETA_PROMO_CODE", "BETA50")

DOMAIN = os.getenv("DOMAIN", "http://localhost:5173")


class StripeService:
    """Service class for handling Stripe operations"""

    @staticmethod
    def create_checkout_session(
        price_id: str,
        user_id: str,
        user_email: str,
        success_url: str = None,
        cancel_url: str = None,
        apply_beta_discount: bool = False
    ) -> Dict[str, Any]:
        """
        Create a Stripe Checkout Session for subscription

        Args:
            price_id: Stripe price ID (pro or elite tier)
            user_id: Internal user ID
            user_email: User's email address
            success_url: URL to redirect on successful payment
            cancel_url: URL to redirect on cancelled payment
            apply_beta_discount: If True, automatically apply beta promo code

        Returns:
            Dictionary with session_id and checkout URL
        """
        try:
            # Set default URLs if not provided
            if not success_url:
                success_url = f"{DOMAIN}/subscription/success?session_id={{CHECKOUT_SESSION_ID}}"
            if not cancel_url:
                cancel_url = f"{DOMAIN}/subscription/cancel"

            # Build session parameters
            session_params = {
                'customer_email': user_email,
                'client_reference_id': user_id,  # Link to our internal user ID
                'payment_method_types': ['card'],
                'line_items': [{
                    'price': price_id,
                    'quantity': 1,
                }],
                'mode': 'subscription',
                'success_url': success_url,
                'cancel_url': cancel_url,
                'metadata': {
                    'user_id': user_id,
                },
                # Enable customer portal access
                'subscription_data': {
                    'metadata': {
                        'user_id': user_id,
                    },
                    # No trial - immediate payment with 50% discount
                },
                # Collect billing address
                'billing_address_collection': 'required',
            }

            # Apply beta promo code if requested
            if apply_beta_discount and STRIPE_BETA_PROMO_CODE:
                session_params['discounts'] = [{
                    'promotion_code': STRIPE_BETA_PROMO_CODE
                }]
                print(f"Applying beta promo code: {STRIPE_BETA_PROMO_CODE}")

            # Create checkout session
            session = stripe.checkout.Session.create(**session_params)

            return {
                'session_id': session.id,
                'url': session.url
            }

        except stripe.StripeError as e:
            raise Exception(f"Stripe error: {str(e)}")

    @staticmethod
    def create_portal_session(customer_id: str, return_url: str = None) -> Dict[str, str]:
        """
        Create a Stripe Customer Portal Session
        Allows users to manage their subscription, payment methods, and view invoices
        
        Args:
            customer_id: Stripe customer ID
            return_url: URL to return to after portal session
            
        Returns:
            Dictionary with portal URL
        """
        try:
            if not return_url:
                return_url = f"{DOMAIN}/subscription"

            session = stripe.billing_portal.Session.create(
                customer=customer_id,
                return_url=return_url,
            )

            return {'url': session.url}

        except stripe.StripeError as e:
            raise Exception(f"Stripe error: {str(e)}")

    @staticmethod
    def get_subscription(subscription_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve subscription details from Stripe
        
        Args:
            subscription_id: Stripe subscription ID
            
        Returns:
            Dictionary with subscription details
        """
        try:
            subscription = stripe.Subscription.retrieve(subscription_id)
            
            return {
                'id': subscription.id,
                'customer': subscription.customer,
                'status': subscription.status,
                'current_period_start': subscription.current_period_start,
                'current_period_end': subscription.current_period_end,
                'cancel_at_period_end': subscription.cancel_at_period_end,
                'items': [
                    {
                        'id': item.id,
                        'price_id': item.price.id,
                        'product_id': item.price.product
                    }
                    for item in subscription['items']['data']
                ]
            }

        except stripe.StripeError as e:
            print(f"Error retrieving subscription: {str(e)}")
            return None

    @staticmethod
    def retrieve_checkout_session(session_id: str):
        """
        Retrieve a Stripe checkout session

        Args:
            session_id: Stripe checkout session ID

        Returns:
            Stripe Session object or None
        """
        try:
            session = stripe.checkout.Session.retrieve(session_id)
            return session
        except stripe.StripeError as e:
            print(f"Error retrieving checkout session: {str(e)}")
            return None

    @staticmethod
    def get_customer(customer_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve customer details from Stripe
        
        Args:
            customer_id: Stripe customer ID
            
        Returns:
            Dictionary with customer details
        """
        try:
            customer = stripe.Customer.retrieve(customer_id)
            
            return {
                'id': customer.id,
                'email': customer.email,
                'name': customer.name,
                'metadata': customer.metadata
            }

        except stripe.StripeError as e:
            print(f"Error retrieving customer: {str(e)}")
            return None

    @staticmethod
    def cancel_subscription(subscription_id: str, at_period_end: bool = True) -> bool:
        """
        Cancel a subscription
        
        Args:
            subscription_id: Stripe subscription ID
            at_period_end: If True, cancel at end of billing period. If False, cancel immediately.
            
        Returns:
            Boolean indicating success
        """
        try:
            if at_period_end:
                # Schedule cancellation at period end
                stripe.Subscription.modify(
                    subscription_id,
                    cancel_at_period_end=True
                )
            else:
                # Cancel immediately
                stripe.Subscription.delete(subscription_id)
            
            return True

        except stripe.StripeError as e:
            print(f"Error cancelling subscription: {str(e)}")
            return False

    @staticmethod
    def verify_webhook_signature(payload: bytes, sig_header: str) -> Optional[Dict[str, Any]]:
        """
        Verify webhook signature and parse event
        
        Args:
            payload: Raw request body
            sig_header: Stripe-Signature header value
            
        Returns:
            Parsed webhook event or None if invalid
        """
        webhook_secret = os.getenv("STRIPE_WEBHOOK_SECRET")
        
        if not webhook_secret:
            raise Exception("STRIPE_WEBHOOK_SECRET not configured")

        try:
            event = stripe.Webhook.construct_event(
                payload, sig_header, webhook_secret
            )
            return event

        except ValueError:
            # Invalid payload
            print("Invalid webhook payload")
            return None
        except stripe.error.SignatureVerificationError:
            # Invalid signature
            print("Invalid webhook signature")
            return None

    @staticmethod
    def get_price_tier(price_id: str) -> str:
        """
        Determine subscription tier from price ID

        Args:
            price_id: Stripe price ID

        Returns:
            Tier name ('trial', 'beta', 'starter', 'semipro', 'professional', 'elite', 'elitepro')
        """
        if price_id == STRIPE_BETA_PRICE_ID:
            return 'beta'
        elif price_id == STRIPE_STARTER_PRICE_ID:
            return 'starter'
        elif price_id == STRIPE_SEMIPRO_PRICE_ID:
            return 'semipro'
        elif price_id == STRIPE_PROFESSIONAL_PRICE_ID:
            return 'professional'
        elif price_id == STRIPE_ELITE_PRICE_ID:
            return 'elite'
        elif price_id == STRIPE_ELITEPRO_PRICE_ID:
            return 'elitepro'
        else:
            return 'trial'

    @staticmethod
    def create_customer(email: str, user_id: str, name: str = None) -> Optional[str]:
        """
        Create a new Stripe customer
        
        Args:
            email: Customer email
            user_id: Internal user ID
            name: Customer name (optional)
            
        Returns:
            Stripe customer ID or None on error
        """
        try:
            customer = stripe.Customer.create(
                email=email,
                name=name,
                metadata={
                    'user_id': user_id
                }
            )
            
            return customer.id

        except stripe.StripeError as e:
            print(f"Error creating customer: {str(e)}")
            return None

    @staticmethod
    def list_invoices(customer_id: str, limit: int = 10) -> list:
        """
        List invoices for a customer
        
        Args:
            customer_id: Stripe customer ID
            limit: Maximum number of invoices to return
            
        Returns:
            List of invoice dictionaries
        """
        try:
            invoices = stripe.Invoice.list(
                customer=customer_id,
                limit=limit
            )
            
            return [
                {
                    'id': invoice.id,
                    'number': invoice.number,
                    'amount_due': invoice.amount_due / 100,  # Convert cents to dollars
                    'amount_paid': invoice.amount_paid / 100,
                    'status': invoice.status,
                    'created': invoice.created,
                    'invoice_pdf': invoice.invoice_pdf,
                    'hosted_invoice_url': invoice.hosted_invoice_url
                }
                for invoice in invoices.data
            ]

        except stripe.StripeError as e:
            print(f"Error listing invoices: {str(e)}")
            return []


def handle_webhook_event(event: Dict[str, Any]) -> Dict[str, Any]:
    """
    Process Stripe webhook events
    
    Args:
        event: Parsed Stripe webhook event
        
    Returns:
        Dictionary with processing result and data to update in database
    """
    event_type = event['type']
    data = event['data']['object']
    
    result = {
        'event_type': event_type,
        'processed': False,
        'user_id': None,
        'customer_id': None,
        'subscription_id': None,
        'tier': None,
        'status': None,
        'action': None
    }
    
    try:
        if event_type == 'customer.subscription.created':
            # New subscription created
            result['user_id'] = data.get('metadata', {}).get('user_id')
            result['customer_id'] = data['customer']
            result['subscription_id'] = data['id']
            result['status'] = data['status']
            
            # Determine tier from price
            price_id = data['items']['data'][0]['price']['id']
            result['tier'] = StripeService.get_price_tier(price_id)
            result['action'] = 'create_subscription'
            result['processed'] = True
            
        elif event_type == 'customer.subscription.updated':
            # Subscription updated (upgrade/downgrade/renewal)
            result['user_id'] = data.get('metadata', {}).get('user_id')
            result['customer_id'] = data['customer']
            result['subscription_id'] = data['id']
            result['status'] = data['status']
            
            price_id = data['items']['data'][0]['price']['id']
            result['tier'] = StripeService.get_price_tier(price_id)
            result['action'] = 'update_subscription'
            result['processed'] = True
            
        elif event_type == 'customer.subscription.deleted':
            # Subscription cancelled/expired
            result['user_id'] = data.get('metadata', {}).get('user_id')
            result['customer_id'] = data['customer']
            result['subscription_id'] = data['id']
            result['status'] = 'canceled'
            result['tier'] = 'free'
            result['action'] = 'cancel_subscription'
            result['processed'] = True
            
        elif event_type == 'invoice.payment_succeeded':
            # Successful payment
            result['customer_id'] = data['customer']
            result['subscription_id'] = data['subscription']
            result['action'] = 'payment_succeeded'
            result['processed'] = True
            
        elif event_type == 'invoice.payment_failed':
            # Failed payment - may need to downgrade or notify user
            result['customer_id'] = data['customer']
            result['subscription_id'] = data['subscription']
            result['action'] = 'payment_failed'
            result['processed'] = True
            
    except Exception as e:
        print(f"Error processing webhook event: {str(e)}")
        result['error'] = str(e)
    
    return result
