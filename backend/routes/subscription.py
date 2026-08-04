"""Stripe subscription routes — checkout, portal, webhook, status, features"""
import os
import stripe
import logging
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import RedirectResponse
from pydantic import BaseModel

from stripe_service import StripeService, handle_webhook_event
from subscription_db import SubscriptionDB, get_db_connection
from db_utils import get_optimized_connection
import auth

logger = logging.getLogger(__name__)

router = APIRouter(tags=["subscription"])


# ========== REQUEST MODELS ==========

class CheckoutSessionRequest(BaseModel):
    price_id: str
    user_id: str
    user_email: str
    apply_beta_discount: bool = False


class PortalSessionRequest(BaseModel):
    user_id: str


# ========== ENDPOINTS ==========

@router.post("/api/stripe/create-checkout-session")
async def create_checkout_session(request: CheckoutSessionRequest):
    """Create a Stripe Checkout Session for subscription."""
    try:
        user = SubscriptionDB.get_user(request.user_id)
        if not user:
            SubscriptionDB.create_or_update_user(
                user_id=request.user_id,
                email=request.user_email
            )
            user = SubscriptionDB.get_user(request.user_id)

        if not user.get('stripe_customer_id'):
            customer_id = StripeService.create_customer(
                email=request.user_email,
                user_id=request.user_id
            )
            if customer_id:
                SubscriptionDB.create_or_update_user(
                    user_id=request.user_id,
                    email=request.user_email,
                    stripe_customer_id=customer_id
                )

        session = StripeService.create_checkout_session(
            price_id=request.price_id,
            user_id=request.user_id,
            user_email=request.user_email,
            apply_beta_discount=request.apply_beta_discount
        )

        return {
            "success": True,
            "session_id": session['session_id'],
            "url": session['url']
        }

    except Exception as e:
        logger.error(f"Error creating checkout session: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to create checkout session: {str(e)}")


@router.post("/api/stripe/create-portal-session")
async def create_portal_session(request: PortalSessionRequest):
    """Create a Stripe Customer Portal Session for subscription management."""
    try:
        user = SubscriptionDB.get_user(request.user_id)
        if not user or not user.get('stripe_customer_id'):
            raise HTTPException(status_code=404, detail="No subscription found for user")

        session = StripeService.create_portal_session(
            customer_id=user['stripe_customer_id']
        )

        return {"success": True, "url": session['url']}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating portal session: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to create portal session: {str(e)}")


@router.post("/api/stripe/webhook")
async def stripe_webhook(request: Request):
    """
    Handle Stripe webhook events.
    Updates subscription status in database based on Stripe events.
    """
    try:
        payload = await request.body()
        sig_header = request.headers.get('stripe-signature')

        if not sig_header:
            raise HTTPException(status_code=400, detail="Missing signature header")

        event = StripeService.verify_webhook_signature(payload, sig_header)
        if not event:
            raise HTTPException(status_code=400, detail="Invalid webhook signature")

        result = handle_webhook_event(event)

        if result['processed']:
            if result['action'] == 'create_subscription':
                user_id = result['user_id']
                if not user_id and result['customer_id']:
                    with get_db_connection() as conn:
                        cursor = conn.cursor()
                        cursor.execute(
                            'SELECT id FROM users WHERE stripe_customer_id = ?',
                            (result['customer_id'],)
                        )
                        row = cursor.fetchone()
                        if row:
                            user_id = row['id']
                            logger.info(f"Found user_id {user_id} for customer {result['customer_id']}")

                if user_id:
                    SubscriptionDB.create_subscription(
                        user_id=user_id,
                        stripe_subscription_id=result['subscription_id'],
                        stripe_customer_id=result['customer_id'],
                        tier=result['tier'],
                        status=result['status']
                    )
                    logger.info(f"Created subscription for user {user_id}, tier {result['tier']}")

                    # Admin notification — non-critical, failures are logged and swallowed
                    try:
                        users = auth.load_users()
                        if user_id in users:
                            user_data = users[user_id]
                            amount = result.get('amount', 0) / 100 if result.get('amount') else 0
                            logger.info(
                                f"Payment received: user={user_id} "
                                f"email={user_data.get('email', 'unknown')} "
                                f"tier={result['tier']} amount=${amount:.2f}"
                            )
                    except Exception as notification_error:
                        logger.error(f"Admin notification failed (non-critical): {notification_error}")
                else:
                    logger.warning(f"Could not find user_id for customer {result['customer_id']}")

            elif result['action'] == 'update_subscription':
                SubscriptionDB.update_subscription(
                    stripe_subscription_id=result['subscription_id'],
                    tier=result['tier'],
                    status=result['status']
                )

            elif result['action'] == 'cancel_subscription':
                SubscriptionDB.cancel_subscription(
                    stripe_subscription_id=result['subscription_id']
                )

        return {"received": True}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Webhook error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Webhook processing failed: {str(e)}")


@router.post("/api/subscription/verify-checkout")
async def verify_checkout(request: Request):
    """
    Verify Stripe checkout session and create/update subscription.
    Backup system in case the webhook hasn't fired yet.
    """
    try:
        data = await request.json()
        session_id = data.get('session_id')
        user_id = data.get('user_id')

        if not session_id or not user_id:
            raise HTTPException(status_code=400, detail="Missing session_id or user_id")

        session = StripeService.retrieve_checkout_session(session_id)
        if not session:
            raise HTTPException(status_code=404, detail="Checkout session not found")

        if session.payment_status != 'paid':
            return {
                "success": False,
                "message": "Payment not yet completed",
                "payment_status": session.payment_status
            }

        stripe_subscription_id = session.subscription
        stripe_customer_id = session.customer

        line_items = stripe.checkout.Session.list_line_items(session_id, limit=1)
        if not line_items or not line_items.data:
            raise HTTPException(status_code=500, detail="No line items found in session")

        price_id = line_items.data[0].price.id
        tier = StripeService.get_price_tier(price_id)

        logger.info(f"Verifying checkout for user {user_id}: tier={tier}, subscription_id={stripe_subscription_id}")

        existing_sub = SubscriptionDB.get_subscription(user_id)
        if existing_sub and existing_sub.get('stripe_subscription_id') == stripe_subscription_id:
            return {
                "success": True,
                "message": "Subscription already active",
                "tier": tier,
                "created_by": "webhook"
            }

        SubscriptionDB.create_subscription(
            user_id=user_id,
            stripe_subscription_id=stripe_subscription_id,
            stripe_customer_id=stripe_customer_id,
            tier=tier,
            status='active'
        )

        logger.info(f"Created subscription for user {user_id}, tier {tier} via manual verification")

        return {
            "success": True,
            "message": "Subscription activated",
            "tier": tier,
            "created_by": "manual_verification"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error verifying checkout: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to verify checkout: {str(e)}")


@router.get("/api/subscription/status")
async def get_subscription_status(user_id: str):
    """Get subscription status — tier, status, expiration date."""
    try:
        subscription = SubscriptionDB.get_subscription(user_id)
        if not subscription:
            return {"tier": "free", "status": "none"}

        return {
            "tier": subscription['tier'],
            "status": subscription['status'],
            "current_period_end": subscription.get('current_period_end'),
            "cancel_at_period_end": bool(subscription.get('cancel_at_period_end')),
            "trial_end": subscription.get('trial_end')
        }

    except Exception as e:
        logger.error(f"Error getting subscription status: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get subscription status: {str(e)}")


@router.get("/api/subscription/features")
async def get_subscription_features(user_id: str):
    """Get available features for user's subscription tier."""
    try:
        tier = SubscriptionDB.get_subscription_tier(user_id)

        features = {
            'free': ['live_games_limited', 'basic_odds'],
            'pro': [
                'live_games_limited', 'basic_odds',
                'all_sports', 'alerts', 'arbitrage', 'steam_moves', 'middles',
                'email_notifications', 'unlimited_views'
            ],
            'elite': [
                'live_games_limited', 'basic_odds',
                'all_sports', 'alerts', 'arbitrage', 'steam_moves', 'middles',
                'email_notifications', 'unlimited_views',
                'goalie_pulls', 'api_access', 'sms_notifications', 'custom_alerts',
                'advanced_analytics'
            ]
        }

        return {
            "tier": tier,
            "features": features.get(tier, features['free'])
        }

    except Exception as e:
        logger.error(f"Error getting subscription features: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get subscription features: {str(e)}")


@router.get("/api/subscription/check-access")
async def check_feature_access(user_id: str, feature: str):
    """Check if user has access to a specific feature."""
    try:
        has_access = SubscriptionDB.has_feature_access(user_id, feature)
        return {
            "feature": feature,
            "has_access": has_access,
            "tier": SubscriptionDB.get_subscription_tier(user_id)
        }

    except Exception as e:
        logger.error(f"Error checking feature access: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to check feature access: {str(e)}")


@router.get("/api/upgrade")
async def upgrade_from_email(tier: str, email: str, username: str):
    """
    Upgrade endpoint for email trial reminder links.
    Redirects user to Stripe checkout for selected tier.
    """
    STRIPE_PRICE_IDS = {
        'starter': 'price_1SNuPeR1TzxiBDhG2poLUgpO',
        'semipro': 'price_1SNuQhR1TzxiBDhG1Qe8ZwGN',
        'professional': 'price_1SNuRQR1TzxiBDhGo6UuEf6f',
        'elite': 'price_1SNuRrR1TzxiBDhG2sGWFocn',
        'elitepro': 'price_1SNuSRR1TzxiBDhGaBhjKZXJ',
    }

    try:
        tier_lower = tier.lower()
        if tier_lower not in STRIPE_PRICE_IDS:
            raise HTTPException(status_code=400, detail=f"Invalid tier: {tier}")

        checkout_session = StripeService.create_checkout_session(
            price_id=STRIPE_PRICE_IDS[tier_lower],
            user_id=username,
            user_email=email,
            success_url=f"{os.getenv('DOMAIN', 'https://max-ev-sports.com')}/subscription/success?session_id={{CHECKOUT_SESSION_ID}}",
            cancel_url=f"{os.getenv('DOMAIN', 'https://max-ev-sports.com')}/#/pricing",
            apply_beta_discount=True
        )

        return RedirectResponse(url=checkout_session['url'])

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating upgrade checkout: {str(e)}")
        return RedirectResponse(url=f"{os.getenv('DOMAIN', 'https://max-ev-sports.com')}/#/pricing")


@router.get("/api/subscription/beta-count")
async def get_beta_subscriber_count():
    """Get the count of active beta subscribers (real-time counter for pricing page)."""
    try:
        conn = get_optimized_connection("subscriptions.db")
        cursor = conn.cursor()
        cursor.execute(
            "SELECT COUNT(*) FROM subscriptions WHERE tier = 'beta' AND status = 'active'"
        )
        count = cursor.fetchone()[0]
        conn.close()
        return {"success": True, "count": count}

    except Exception as e:
        logger.error(f"Error fetching beta count: {str(e)}")
        return {"success": False, "count": 0}


@router.post("/api/waitlist/add")
async def add_to_waitlist(request: Request):
    """Add email to waitlist for full launch notification."""
    try:
        data = await request.json()
        email = data.get('email')
        tier = data.get('tier', 'full_launch')
        price = data.get('price', 29.99)

        if not email:
            raise HTTPException(status_code=400, detail="Email is required")

        conn = get_optimized_connection("subscriptions.db")
        cursor = conn.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS waitlist (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT UNIQUE NOT NULL,
                tier TEXT,
                price REAL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        cursor.execute(
            "INSERT OR IGNORE INTO waitlist (email, tier, price) VALUES (?, ?, ?)",
            (email, tier, price)
        )
        conn.commit()
        conn.close()

        logger.info(f"Added {email} to waitlist for {tier} at ${price}")
        return {"success": True, "message": "Successfully added to waitlist"}

    except Exception as e:
        logger.error(f"Error adding to waitlist: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to add to waitlist: {str(e)}")
